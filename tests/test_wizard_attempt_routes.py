import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException, Response
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import (
    Case,
    CaseMembership,
    SettlementLedgerEvent,
    SettlementNegotiationAttempt,
    SettlementScenarioRun,
    SettlementScenarioSelection,
    User,
)
from app.wizard_attempt import create_wizard_attempt, read_wizard_attempt


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


DRAFT = {
    "schema_version": 1,
    "filed": "yes",
    "role": "respondent",
    "dates": {
        "marriage": {"date": "2015-06-01"},
        "separation": {"date": "2024-02-15"},
        "petition": {"date": "2024-03-01"},
    },
    "finances": [
        {"id": "a1", "kind": "asset", "description": "Family home", "amount": "512345.67",
         "acquired_date": "2016-04-20"},
        {"id": "a2", "kind": "asset", "description": "Savings", "amount": "1000.10"},
        {"id": "d1", "kind": "debt", "description": "Home loan", "amount": "301000"},
        {"id": "a3", "kind": "asset", "description": "No amount"},
    ],
    "issues": [{"id": "i1", "topic": "Home", "outcome": "I keep the house"}],
    "agreements": [],
}


class WizardAttemptRouteTests(unittest.TestCase):
    def setUp(self) -> None:
        self._server_defaults = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                default = column.server_default
                if default is not None and "::" in str(getattr(default, "arg", "")):
                    self._server_defaults.append((column, default))
                    column.server_default = None
        engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.owner = User(email="owner@example.com", status="active")
        self.other = User(email="other@example.com", status="active")
        self.db.add_all([self.owner, self.other])
        self.db.flush()
        self.case = Case(
            status="draft",
            metadata_json={"case_title": "XYZ vs ABC", "workflow_mode": "wizard"},
            wizard_intake_json=DRAFT,
            wizard_intake_revision=4,
        )
        self.db.add(self.case)
        self.db.flush()
        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.owner.id, role="owner"))
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        for column, default in self._server_defaults:
            column.server_default = default

    def _count(self, model) -> int:
        return self.db.scalar(select(func.count()).select_from(model))

    def _rows(self) -> tuple[int, int, int, int]:
        return tuple(
            self._count(model)
            for model in (
                SettlementLedgerEvent,
                SettlementScenarioRun,
                SettlementScenarioSelection,
                SettlementNegotiationAttempt,
            )
        )

    def _post(self, user=None):
        return create_wizard_attempt(self.case.id, Response(), user or self.owner, self.db)

    def test_creates_attempt_one_with_the_entered_values(self) -> None:
        result = self._post()

        self.assertEqual(result.status, "created")
        self.assertTrue(result.attempt_exists)
        self.assertEqual(self._rows(), (3, 1, 1, 1))
        events = self.db.scalars(select(SettlementLedgerEvent)).all()
        amounts = {row.asset_name: row.event_json["amount_cents"] for row in events}
        self.assertEqual(
            amounts, {"Family home": 51234567, "Savings": 100010, "Home loan": 30100000}
        )
        self.assertTrue(all(row.event_json["provenance"] == "user_reported" for row in events))
        self.assertTrue(all(row.event_json["event_type"] == "valuation" for row in events))
        self.assertEqual(self.db.get(Case, self.case.id).settlement_revision, 3)

    def test_attempt_state_carries_role_dates_terms_and_axes(self) -> None:
        self._post()

        attempt = self.db.scalar(select(SettlementNegotiationAttempt))
        state = attempt.editable_state_json
        self.assertEqual(attempt.attempt_ordinal, 1)
        self.assertEqual((state["offer_from"], state["offer_to"]), ("Respondent", "Petitioner"))
        self.assertEqual(state["proposal_terms"], ["Issue — Home: I keep the house"])
        self.assertEqual(
            [m["name"] for m in state["milestones"]], ["Marriage", "Separation", "Petition filed"]
        )
        window = state["scenario_assumptions"]["relationship_windows"][0]
        self.assertEqual(window["label"], "As entered in your case information")
        self.assertEqual(state["proposed_values"], [])

    def test_engine_reports_each_entered_amount_as_unresolved_total(self) -> None:
        self._post()

        selection = self.db.scalar(select(SettlementScenarioSelection))
        text = str(selection.scenario_result_json)
        self.assertIn("unresolved", text)
        for cents in (51234567, 100010, 30100000):
            self.assertIn(str(cents), text)

    def test_snapshot_ledger_matches_the_entered_assets(self) -> None:
        self._post()

        attempt = self.db.scalar(select(SettlementNegotiationAttempt))
        ledger = attempt.snapshot_json["settlement_ledger"]
        self.assertEqual(
            sorted(item["asset_name"] for item in ledger), ["Family home", "Home loan", "Savings"]
        )

    def test_report_is_stored_with_the_case_and_excludes_unusable_entries(self) -> None:
        result = self._post()

        stored = self.db.get(Case, self.case.id).metadata_json
        self.assertEqual(stored["case_title"], "XYZ vs ABC")
        self.assertEqual(stored["wizard_attempt"], result.report)
        self.assertEqual(result.report["wizard_revision"], 4)
        self.assertEqual(
            result.report["excluded"],
            [{"kind": "asset", "label": "No amount", "reason": "No amount was entered."}],
        )

    def test_repeat_calls_return_exists_and_change_nothing(self) -> None:
        self._post()
        before = self._rows()
        revision = self.db.get(Case, self.case.id).settlement_revision

        second = self._post()

        self.assertEqual(second.status, "exists")
        self.assertEqual(self._rows(), before)
        self.assertEqual(self.db.get(Case, self.case.id).settlement_revision, revision)

    def test_later_wizard_edits_do_not_change_the_attempt(self) -> None:
        self._post()
        self.case.wizard_intake_json = {**DRAFT, "finances": [{"id": "a1", "kind": "asset", "amount": "1"}]}
        self.db.commit()

        self.assertEqual(self._post().status, "exists")
        ledger = self.db.scalars(select(SettlementLedgerEvent)).all()
        self.assertEqual(len(ledger), 3)

    def test_missing_dates_or_amounts_write_nothing(self) -> None:
        self.case.wizard_intake_json = {
            "schema_version": 1,
            "dates": {"marriage": {"unknown": True}},
            "finances": [{"id": "x", "kind": "asset", "description": "None"}],
        }
        self.db.commit()

        result = self._post()

        self.assertEqual(result.status, "needs_information")
        self.assertFalse(result.attempt_exists)
        self.assertEqual(len(result.needs), 3)
        self.assertEqual(self._rows(), (0, 0, 0, 0))
        self.assertEqual(self.db.get(Case, self.case.id).settlement_revision, 0)

    def test_existing_attempt_from_another_path_is_reported_as_exists(self) -> None:
        self._post()
        self.case.wizard_intake_json = {}
        self.db.commit()

        self.assertEqual(self._post().status, "exists")

    def test_existing_ledger_without_an_attempt_is_not_mixed_in(self) -> None:
        self._post()
        self.db.query(SettlementNegotiationAttempt).delete()
        self.db.query(SettlementScenarioSelection).delete()
        self.db.commit()

        result = self._post()

        self.assertEqual(result.status, "needs_information")
        self.assertIn("already has settlement ledger entries", result.needs[0])

    def test_failure_leaves_nothing_behind_and_a_retry_works(self) -> None:
        with patch.object(self.db, "commit", side_effect=SQLAlchemyError("down")):
            with self.assertRaises(HTTPException) as caught:
                self._post()

        self.assertEqual(caught.exception.status_code, 503)
        self.db.expire_all()
        self.assertEqual(self._rows(), (0, 0, 0, 0))
        self.assertEqual(self.db.get(Case, self.case.id).settlement_revision, 0)
        self.assertEqual(self._post().status, "created")

    def test_calculation_failure_is_all_or_nothing(self) -> None:
        with patch("app.wizard_attempt.calculate_scenario", side_effect=ValueError("bad")):
            with self.assertRaises(HTTPException) as caught:
                self._post()

        self.assertEqual(caught.exception.status_code, 422)
        self.db.expire_all()
        self.assertEqual(self._rows(), (0, 0, 0, 0))

    def test_access_rules(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            self._post(self.other)
        self.assertEqual(caught.exception.status_code, 404)

        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.other.id, role="viewer"))
        self.db.commit()
        with self.assertRaises(HTTPException) as caught:
            self._post(self.other)
        self.assertEqual(caught.exception.status_code, 403)

        with self.assertRaises(HTTPException) as caught:
            create_wizard_attempt(uuid4(), Response(), self.owner, self.db)
        self.assertEqual(caught.exception.status_code, 404)
        self.assertEqual(self._rows(), (0, 0, 0, 0))

    def test_closed_case_is_refused(self) -> None:
        from datetime import UTC, datetime

        self.case.closed_at = datetime.now(UTC)
        self.db.commit()

        with self.assertRaises(HTTPException) as caught:
            self._post()

        self.assertEqual(caught.exception.status_code, 409)
        self.assertEqual(self._rows(), (0, 0, 0, 0))

    def test_get_reports_needs_and_then_the_stored_report(self) -> None:
        before = read_wizard_attempt(self.case.id, Response(), self.owner, self.db)
        self.assertEqual((before.status, before.attempt_exists, before.needs), ("created", False, []))
        self.assertIsNone(before.report)

        self._post()
        after = read_wizard_attempt(self.case.id, Response(), self.owner, self.db)

        self.assertEqual((after.status, after.attempt_exists), ("exists", True))
        self.assertEqual(after.report["included"][0]["label"], "Family home")

    def test_get_is_read_only_for_viewers_and_hidden_from_strangers(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            read_wizard_attempt(self.case.id, Response(), self.other, self.db)
        self.assertEqual(caught.exception.status_code, 404)
        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.other.id, role="viewer"))
        self.db.commit()

        self.assertFalse(read_wizard_attempt(self.case.id, Response(), self.other, self.db).attempt_exists)
        self.assertEqual(self._rows(), (0, 0, 0, 0))


if __name__ == "__main__":
    unittest.main()
