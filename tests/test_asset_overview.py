import unittest
from io import BytesIO
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import MagicMock, patch
from uuid import uuid4
from docx import Document as WordDocument
from openpyxl import load_workbook

from fastapi import HTTPException, Response
from fastapi.testclient import TestClient
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.asset_overview import AssetOverviewRead, AssetOverviewUpdate, OverviewScenarioExport
from app.config import Settings
from app.main import CaseCreate, app, save_case_asset_overview, download_asset_overview_scenario
from app.models import Case


class AssetOverviewTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case = Case(
            id=uuid4(), status="draft", metadata_json={"case_title": "Synthetic"},
            property_assets=[], relationship_milestones={}, asset_liability_inventory={},
        )
        self.user = SimpleNamespace(id=uuid4())
        self.db = MagicMock(spec=Session)
        self.db.scalar.side_effect = [self.case, None]
        self.payload = AssetOverviewUpdate.model_validate({
            "expected_revision": 0,
            "overview": {
                "snapshots": [{"date": "2025-01-01", "balances": [
                    {"category": "Savings", "you_cents": 12345, "other_cents": None},
                ]}],
                "milestones": [{"label": "User-entered date", "date": "2025-01-01"}],
            },
        })

    def save(self, membership: str | None = "owner") -> AssetOverviewRead:
        role = None if membership is None else SimpleNamespace(role=membership)
        with patch("app.main.resolve_case_access", return_value=role):
            return save_case_asset_overview(self.case.id, self.payload, self.response, self.user, self.db)

    def test_saves_explicit_cents_and_missing_values_without_changing_source_records(self) -> None:
        self.response = Response()
        result = self.save()
        self.assertEqual(result.revision, 1)
        self.assertEqual(result.overview.snapshots[0].balances[0].you_cents, 12345)
        self.assertIsNone(result.overview.snapshots[0].balances[0].other_cents)
        self.assertEqual(self.case.metadata_json["case_title"], "Synthetic")
        self.assertEqual(self.case.metadata_json["asset_overview"]["revision"], 1)
        self.assertEqual(self.case.property_assets, [])
        self.assertEqual(self.response.headers["Cache-Control"], "no-store")
        self.assertIsNotNone(self.db.scalar.call_args_list[0].args[0]._for_update_arg)
        self.db.commit.assert_called_once()

    def test_conflict_preserves_existing_values(self) -> None:
        self.response = Response()
        self.case.metadata_json["asset_overview"] = {"revision": 1, "overview": {}}
        with self.assertRaises(HTTPException) as error:
            self.save()
        self.assertEqual(error.exception.status_code, 409)
        self.db.commit.assert_not_called()
        self.assertEqual(self.case.metadata_json["asset_overview"]["revision"], 1)

    def test_non_members_and_non_owners_cannot_write(self) -> None:
        self.response = Response()
        for membership, status in [(None, 404), ("delegate", 403)]:
            with self.subTest(membership=membership):
                self.db.scalar.side_effect = [self.case, None]
                with self.assertRaises(HTTPException) as error:
                    self.save(membership)
                self.assertEqual(error.exception.status_code, status)
        self.db.commit.assert_not_called()

    def test_closed_and_finalized_cases_cannot_write(self) -> None:
        self.response = Response()
        for closed, status in [(datetime.now(UTC), "draft"), (None, "finalized")]:
            with self.subTest(status=status):
                self.case.closed_at, self.case.status = closed, status
                self.db.scalar.side_effect = [self.case, None]
                with self.assertRaises(HTTPException) as error:
                    self.save()
                self.assertEqual(error.exception.status_code, 409)
        self.db.commit.assert_not_called()

    def test_frozen_and_finalized_attempts_cannot_write(self) -> None:
        self.response = Response()
        for frozen, finalized in [(datetime.now(UTC), None), (None, datetime.now(UTC))]:
            with self.subTest(frozen=frozen):
                self.db.scalar.side_effect = [self.case, SimpleNamespace(frozen_at=frozen, finalized_at=finalized)]
                with self.assertRaises(HTTPException) as error:
                    self.save()
                self.assertEqual(error.exception.status_code, 409)
        self.db.commit.assert_not_called()

    def test_reopened_case_cannot_edit_asset_values_even_without_a_frozen_attempt(self) -> None:
        self.response = Response()
        self.case.attempts_locked_at = datetime.now(UTC)
        with self.assertRaises(HTTPException) as error:
            self.save()
        self.assertEqual(error.exception.status_code, 409)
        self.db.commit.assert_not_called()
        self.assertNotIn("asset_overview", self.case.metadata_json)

    def test_storage_failure_is_logged_rolled_back_and_retryable(self) -> None:
        self.response = Response()
        self.db.commit.side_effect = SQLAlchemyError("Synthetic")
        with patch("app.main.log_failure_event") as log:
            with self.assertRaises(HTTPException) as error:
                self.save()
        self.assertEqual(error.exception.status_code, 503)
        self.db.rollback.assert_called_once()
        log.assert_called_once()

    def test_invalid_dates_duplicate_categories_and_non_integer_cents_are_rejected(self) -> None:
        for snapshot in [
            {"date": "invalid", "balances": []},
            {"date": "2025-01-01", "balances": [{"category": "A"}, {"category": "A"}]},
            {"date": "2025-01-01", "balances": [{"category": "A", "you_cents": True}]},
            {"date": "2025-01-01", "balances": [{"category": "A", "you_cents": 1.5}]},
            {"date": "2025-01-01", "balances": [{"category": " ", "you_cents": 1}]},
            {"date": "2025-01-01", "balances": [{"category": "A", "you_cents": 10**14 + 1}]},
        ]:
            with self.subTest(snapshot=snapshot), self.assertRaises(ValidationError):
                AssetOverviewUpdate.model_validate({"expected_revision": 0, "overview": {"snapshots": [snapshot]}})

    def test_duplicate_snapshot_dates_and_overflow_totals_are_rejected(self) -> None:
        for snapshots in [
            [{"date": "2025-01-01"}, {"date": "2025-01-01"}],
            [{"date": "2025-01-01", "balances": [
                {"category": str(index), "you_cents": 10**14, "other_cents": 0} for index in range(100)
            ]}],
        ]:
            with self.subTest(count=len(snapshots)), self.assertRaises(ValidationError):
                AssetOverviewUpdate.model_validate({"expected_revision": 0, "overview": {"snapshots": snapshots}})

    def test_case_creation_cannot_bypass_the_revisioned_write_endpoint(self) -> None:
        with self.assertRaises(ValidationError):
            CaseCreate.model_validate({"metadata": {"asset_overview": {"revision": 999}}})

    def test_endpoint_requires_authentication(self) -> None:
        settings = Settings(
            auth_enabled=True, case_data_enabled=True,
            auth_jwt_secret="synthetic-signing-secret-that-is-long-enough",
            s3_endpoint_url="http://127.0.0.1:5000",
        )
        with patch("app.main.settings", settings):
            response = TestClient(app).put(f"/cases/{self.case.id}/asset-overview", json=self.payload.model_dump(mode="json"))
        self.assertEqual(response.status_code, 401)


class ScenarioDraftDownloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.saved = {"revision": 3, "overview": {"snapshots": [
            {"date": "2020-01-01", "balances": [
                {"category": "Home equity", "you_cents": 10000, "other_cents": 20000},
                *[{"category": category, "you_cents": 0, "other_cents": 0} for category in (
                    "Retirement accounts", "Cash and savings", "Vehicles", "Debt", "=Unsafe formula",
                )],
            ]},
            {"date": "2023-01-01", "balances": [
                {"category": "Home equity", "you_cents": 40000, "other_cents": 50000},
                *[{"category": category, "you_cents": 0, "other_cents": 0} for category in (
                    "Retirement accounts", "Cash and savings", "Vehicles", "Debt", "=Unsafe formula",
                )],
            ]},
        ]}}
        self.case = Case(id=uuid4(), status="draft", metadata_json={"asset_overview": self.saved})
        self.user = SimpleNamespace(id=uuid4())
        self.db = MagicMock(spec=Session)
        self.db.scalar.return_value = None
        self.selection = OverviewScenarioExport.model_validate({
            "expected_revision": 3, "attempt_ordinal": 1, "start_date": "2020-01-01",
            "end_date": "2023-01-01", "community_share_bps": 5500,
        })

    def download(self, format, role="owner"):
        membership = SimpleNamespace(role=role) if role is not None else None
        self.db.scalar.side_effect = [self.case, self.db.scalar.return_value]
        with patch("app.main.record_download"), patch("app.main._require_real_case_exports"), patch(
            "app.main.resolve_case_access", return_value=membership,
        ):
            return download_asset_overview_scenario(
                self.case.id, format, self.selection, self.user, self.db,
            )

    def test_word_and_excel_contain_saved_dates_selected_share_and_exact_totals(self) -> None:
        word = self.download("docx")
        self.assertEqual(word.headers["Cache-Control"], "no-store")
        self.assertIn("cr2a-proposal-draft.docx", word.headers["Content-Disposition"])
        text = "\n".join(p.text for p in WordDocument(BytesIO(word.body)).paragraphs)
        for expected in ("2020-01-01", "2023-01-01", "55%", "$430.00", "$470.00", "UNSIGNED", "not legal classifications"):
            self.assertIn(expected, text)
        excel = self.download("xlsx")
        self.assertIn("property-schedule-draft.xlsx", excel.headers["Content-Disposition"])
        workbook = load_workbook(BytesIO(excel.body))
        rows = dict(workbook["Selected scenario"].iter_rows(min_row=5, max_col=2, values_only=True))
        self.assertEqual(rows["Illustrative net to you"], "$430.00")
        self.assertEqual(rows["Illustrative net to other party"], "$470.00")
        self.assertEqual(workbook["Property schedule"]["C2"].value, 100)
        self.assertEqual(workbook["Property schedule"]["C8"].value, 400)
        self.assertEqual(workbook["Property schedule"]["B7"].data_type, "s")
        self.db.commit.assert_not_called()
        self.assertEqual(self.case.metadata_json["asset_overview"], self.saved)

    def test_all_three_scenario_shares_use_net_change_not_entire_balance(self) -> None:
        for share, you, other in [(4500, "$370.00", "$530.00"), (5000, "$400.00", "$500.00"), (5500, "$430.00", "$470.00")]:
            self.selection = self.selection.model_copy(update={"community_share_bps": share})
            workbook = load_workbook(BytesIO(self.download("xlsx").body))
            rows = dict(workbook["Selected scenario"].iter_rows(min_row=5, max_col=2, values_only=True))
            self.assertEqual(rows["Illustrative net to you"], you)
            self.assertEqual(rows["Illustrative net to other party"], other)

    def test_missing_balances_wrong_dates_and_stale_revision_fail_without_mutation(self) -> None:
        for changes, status in [
            ({"expected_revision": 2}, 409),
            ({"start_date": "2021-01-01"}, 422),
            ({"attempt_ordinal": 2}, 409),
        ]:
            original = self.selection
            self.selection = OverviewScenarioExport.model_validate({
                **original.model_dump(mode="json"), **changes,
            })
            with self.assertRaises(HTTPException) as error:
                self.download("docx")
            self.assertEqual(error.exception.status_code, status)
            self.selection = original
        self.saved["overview"]["snapshots"][0]["balances"][0]["other_cents"] = None
        with self.assertRaises(HTTPException) as error:
            self.download("xlsx")
        self.assertEqual(error.exception.status_code, 422)
        self.db.commit.assert_not_called()

    def test_downloads_reject_non_members_and_non_owners(self) -> None:
        for role, status in [(None, 404), ("viewer", 403)]:
            with self.assertRaises(HTTPException) as error:
                self.download("docx", role)
            self.assertEqual(error.exception.status_code, status)

    def test_frozen_attempt_exports_its_saved_snapshot_not_new_live_values(self) -> None:
        self.db.scalar.return_value = SimpleNamespace(
            attempt_ordinal=1, frozen_at=datetime.now(UTC), finalized_at=None,
            finalized_snapshot_json=None,
            frozen_snapshot_json={"case_profile": {"metadata": {"asset_overview": self.saved}}},
            snapshot_json={},
        )
        self.case.metadata_json = {"asset_overview": {"revision": 99, "overview": {}}}
        text = "\n".join(p.text for p in WordDocument(BytesIO(self.download("docx").body)).paragraphs)
        self.assertIn("$430.00", text)
        self.db.commit.assert_not_called()

    def test_database_failure_is_logged_and_download_remains_retryable(self) -> None:
        self.db.scalar.return_value = None
        with patch("app.main.render_overview_scenario_draft", side_effect=SQLAlchemyError("Synthetic")):
            with patch("app.main.log_failure_event") as log, self.assertRaises(HTTPException) as error:
                self.download("docx")
        self.assertEqual(error.exception.status_code, 503)
        self.db.rollback.assert_called_once()
        log.assert_called_once()
