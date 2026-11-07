import importlib.util
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import FastAPI, HTTPException, Response
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.database import get_db
from app.auth_routes import require_current_user
from app.models import Case, CaseMembership, User
from app.wizard_intake import (
    WizardIntakeDraft,
    WizardIntakeUpdate,
    read_wizard_intake,
    router,
    update_wizard_intake,
)


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0025_account_backed_wizard_intake.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "account_backed_wizard_intake_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class WizardIntakeValidationTests(unittest.TestCase):
    def test_empty_draft_has_a_stable_versioned_shape(self) -> None:
        draft = WizardIntakeDraft()

        self.assertEqual(draft.schema_version, 1)
        self.assertIsNone(draft.filed)
        self.assertIsNone(draft.role)
        self.assertEqual(draft.finances, [])
        self.assertEqual(draft.issues, [])
        self.assertEqual(draft.agreements, [])

    def test_accepts_wizard_fields_and_normalizes_blank_optional_values(self) -> None:
        draft = WizardIntakeDraft.model_validate({
            "filed": "yes",
            "role": "petitioner",
            "dates": {
                "cohabitation": {"date": "", "unknown": True},
                "marriage": {"date": "2020-05-01", "unknown": False},
            },
            "finances": [{
                "id": "finance-1",
                "kind": "asset",
                "category": "Home",
                "description": "Family residence",
                "acquired_date": "2020-06-01",
                "acquisition_method": "",
                "amount": "125.50",
                "owners": "Both parties",
                "holding": "",
            }],
            "issues": [{"id": "issue-1", "topic": "Residence", "outcome": "Sell"}],
            "agreements": [{"id": "agreement-1", "summary": "Temporary use", "date": ""}],
        })

        self.assertIsNone(draft.dates.cohabitation.date)
        self.assertTrue(draft.dates.cohabitation.unknown)
        self.assertEqual(draft.finances[0].acquisition_method, None)
        self.assertEqual(str(draft.finances[0].amount), "125.50")
        self.assertIsNone(draft.agreements[0].date)

    def test_rejects_invalid_values_and_browser_file_payloads(self) -> None:
        invalid_drafts = (
            {"role": "attorney"},
            {"dates": {"marriage": {"date": "2020-02-30"}}},
            {"finances": [{"id": "x", "kind": "asset", "amount": "-1"}]},
            {"agreements": [{"id": "same"}, {"id": "same"}]},
            {"issues": [{"id": "x", "attachments": [{"name": "evidence.pdf"}]}]},
            {"unexpected": True},
        )

        for draft in invalid_drafts:
            with self.subTest(draft=draft), self.assertRaises(ValidationError):
                WizardIntakeDraft.model_validate(draft)

    def test_caps_collection_sizes_and_text_lengths(self) -> None:
        with self.assertRaises(ValidationError):
            WizardIntakeDraft(finances=[{"id": str(index)} for index in range(251)])
        with self.assertRaises(ValidationError):
            WizardIntakeDraft(issues=[{"id": "x", "outcome": "x" * 2001}])


class WizardIntakeDatabaseFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._server_defaults = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                default = column.server_default
                if default is not None and "::" in str(getattr(default, "arg", "")):
                    self._server_defaults.append((column, default))
                    column.server_default = None
        self.engine = create_engine(
            "sqlite://",
            poolclass=StaticPool,
            connect_args={"check_same_thread": False},
        )
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)
        self.user = User(
            email="owner@example.com",
            password_hash="test-hash",
            status="active",
        )
        self.other_user = User(
            email="other@example.com",
            password_hash="test-hash",
            status="active",
        )
        self.case = Case(status="draft")
        self.db.add_all([self.user, self.other_user, self.case])
        self.db.flush()
        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.user.id, role="owner"))
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        for column, default in self._server_defaults:
            column.server_default = default


class WizardIntakeRouteTests(WizardIntakeDatabaseFixture):
    def test_get_returns_empty_draft_and_disables_caching(self) -> None:
        response = Response()

        result = read_wizard_intake(self.case.id, response, self.user, self.db)

        self.assertEqual(result.revision, 0)
        self.assertEqual(result.draft.schema_version, 1)
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_put_persists_draft_and_increments_revision(self) -> None:
        update = WizardIntakeUpdate(
            expected_revision=0,
            draft=WizardIntakeDraft(
                filed="yes",
                role="respondent",
                issues=[{"id": "issue-1", "topic": "Property", "outcome": "Sell"}],
            ),
        )

        result = update_wizard_intake(self.case.id, update, self.user, self.db)

        self.assertEqual(result.revision, 1)
        self.assertEqual(result.draft.role, "respondent")
        self.assertEqual(self.case.wizard_intake_revision, 1)
        self.assertEqual(self.case.wizard_intake_json["issues"][0]["topic"], "Property")

    def test_put_rejects_stale_revision_without_overwriting_saved_draft(self) -> None:
        self.case.wizard_intake_json = {"schema_version": 1, "filed": "yes"}
        self.case.wizard_intake_revision = 3
        self.db.commit()
        update = WizardIntakeUpdate(
            expected_revision=2,
            draft=WizardIntakeDraft(filed="no"),
        )

        with self.assertRaises(HTTPException) as raised:
            update_wizard_intake(self.case.id, update, self.user, self.db)

        self.assertEqual(raised.exception.status_code, 409)
        self.db.refresh(self.case)
        self.assertEqual(self.case.wizard_intake_json["filed"], "yes")
        self.assertEqual(self.case.wizard_intake_revision, 3)

    def test_non_member_cannot_read_or_write_case_draft(self) -> None:
        with self.assertRaises(HTTPException) as read_error:
            read_wizard_intake(self.case.id, Response(), self.other_user, self.db)
        self.assertEqual(read_error.exception.status_code, 404)

        with self.assertRaises(HTTPException) as write_error:
            update_wizard_intake(
                self.case.id,
                WizardIntakeUpdate(expected_revision=0, draft=WizardIntakeDraft(filed="yes")),
                self.other_user,
                self.db,
            )
        self.assertEqual(write_error.exception.status_code, 404)

    def test_closed_case_is_read_only(self) -> None:
        self.case.closed_at = datetime.now(UTC)
        self.db.commit()

        with self.assertRaises(HTTPException) as raised:
            update_wizard_intake(
                self.case.id,
                WizardIntakeUpdate(expected_revision=0, draft=WizardIntakeDraft(filed="yes")),
                self.user,
                self.db,
            )

        self.assertEqual(raised.exception.status_code, 409)

    def test_database_failure_rolls_back_and_returns_retryable_error(self) -> None:
        update = WizardIntakeUpdate(
            expected_revision=0,
            draft=WizardIntakeDraft(filed="yes"),
        )
        with (
            patch("app.wizard_intake._authorize_case", return_value=self.case),
            patch("app.wizard_intake._lock_case", return_value=self.case),
            patch.object(self.db, "commit", side_effect=SQLAlchemyError("database unavailable")),
        ):
            with self.assertRaises(HTTPException) as raised:
                update_wizard_intake(self.case.id, update, self.user, self.db)

        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("try again", raised.exception.detail)

    def test_http_routes_round_trip_an_authorized_case_draft(self) -> None:
        api = FastAPI()
        api.include_router(router)
        api.dependency_overrides[require_current_user] = lambda: self.user

        def override_db():
            yield self.db

        api.dependency_overrides[get_db] = override_db
        with TestClient(api) as client:
            response = client.get(f"/cases/{self.case.id}/wizard-intake")
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.headers["cache-control"], "no-store")
            self.assertEqual(response.json()["revision"], 0)

            response = client.put(
                f"/cases/{self.case.id}/wizard-intake",
                json={
                    "expected_revision": 0,
                    "draft": {"filed": "yes", "role": "petitioner"},
                },
            )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["revision"], 1)
        self.assertEqual(response.json()["draft"]["role"], "petitioner")

    def test_http_route_rejects_unknown_case_member(self) -> None:
        api = FastAPI()
        api.include_router(router)
        api.dependency_overrides[require_current_user] = lambda: self.other_user

        def override_db():
            yield self.db

        api.dependency_overrides[get_db] = override_db
        with TestClient(api) as client:
            response = client.get(f"/cases/{self.case.id}/wizard-intake")

        self.assertEqual(response.status_code, 404)


class WizardIntakeMigrationTests(unittest.TestCase):
    def test_migration_adds_and_removes_intake_columns(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()
        added_names = {
            call.args[1].name for call in operations.add_column.call_args_list
        }
        self.assertEqual(
            added_names,
            {"wizard_intake_json", "wizard_intake_revision"},
        )

        with patch.object(migration, "op", operations):
            migration.downgrade()
        self.assertEqual(
            [call.args[1] for call in operations.drop_column.call_args_list],
            ["wizard_intake_revision", "wizard_intake_json"],
        )


class WizardIntakeFrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.page = (
            Path(__file__).resolve().parents[1] / "src" / "app" / "static" / "index.html"
        ).read_text(encoding="utf-8")

    def test_authenticated_wizard_loads_and_saves_the_case_draft(self) -> None:
        initializer = self.page.split(
            "async function initializeWizardDraft()", 1
        )[1].split("function updateWizardGate", 1)[0]
        saver = self.page.split("function saveWizardDraft()", 1)[1].split(
            "function scheduleWizardSave", 1
        )[0]

        self.assertIn("if (preparationCaseId)", initializer)
        self.assertIn("/wizard-intake", initializer)
        self.assertIn("/wizard-intake", saver)
        self.assertIn("expected_revision: wizardServerRevision", saver)
        self.assertIn("draft: wizardDraftToApi()", saver)
        self.assertIn("wizardServerReady = false", initializer)
        self.assertIn("wizardDraftFromApi(result.draft, localSaved)", initializer)

    def test_demo_draft_serialization_stays_local_and_does_not_send_files(self) -> None:
        serializer = self.page.split("function wizardDraftToApi()", 1)[1].split(
            "function wizardDraftFromApi", 1
        )[0]
        initializer = self.page.split(
            "async function initializeWizardDraft()", 1
        )[1].split("function updateWizardGate", 1)[0]

        self.assertNotIn("attachments", serializer)
        self.assertIn("if (preparationCaseId)", initializer)
        self.assertIn("loadWizardDraft()", initializer)
        self.assertIn("saved in this browser", initializer)

    def test_finish_waits_for_server_save_before_leaving_the_case(self) -> None:
        finish_handler = self.page.split(
            'wizardFinish.addEventListener("click", async () =>', 1
        )[1].split('wizardClearButton.addEventListener', 1)[0]

        self.assertIn("const saved = await saveWizardDraft()", finish_handler)
        self.assertIn("if (saved && !preparationCaseId)", finish_handler)
        self.assertNotIn("/#account", finish_handler)


if __name__ == "__main__":
    unittest.main()
