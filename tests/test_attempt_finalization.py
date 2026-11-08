import hashlib
import unittest
from pathlib import Path
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Response
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError

from app.models import DocumentCreditLedgerEntry, SettlementNegotiationAttempt, SettlementProposalVersion
from app.offer_documents import MediationOfferTerms
from app.offer_response import (
    OfferAttemptStateUpdate,
    start_new_proposal_version,
    update_offer_attempt_state,
)
from app.settlement_planning import (
    AssetLedger,
    LedgerEvent,
    RelationshipWindow,
    ScenarioAxes,
    calculate_scenario,
    generate_scenarios,
)
from app.settlement_routes import (
    OfferCreate,
    create_settlement_offer,
    create_settlement_property_schedule,
)


def _scenario_result():
    window = RelationshipWindow(
        id="marriage",
        label="Marriage-only dates",
        relationship_type="marriage_only",
        start_date="2020-01-01",
        separation_date="2024-01-01",
    )
    scenario = generate_scenarios(
        ScenarioAxes(
            relationship_windows=[window],
            tracing_methods=["explicit"],
            community_share_bps=[6_000],
        )
    )[0]
    return calculate_scenario(
        scenario,
        [
            AssetLedger(
                asset_id=uuid4(),
                name="Savings",
                kind="asset",
                events=[
                    LedgerEvent(
                        effective_date="2022-01-01",
                        event_type="contribution",
                        amount_cents=10_000,
                        source_allocations={"community": 10_000},
                        provenance="user_reported",
                    )
                ],
            )
        ],
    )


class FinalDownloadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.result = _scenario_result()
        self.terms = MediationOfferTerms(
            offer_from="Party A",
            offer_to="Party B",
            terms=["Each party retains the property listed in their column."],
        )
        self.user = SimpleNamespace(id=uuid4())
        self.case_id = uuid4()
        self.selection_id = uuid4()
        self.case = SimpleNamespace(
            id=self.case_id,
            profile_revision=3,
            settlement_revision=5,
            first_finalization_used=False,
            attempt_credit_balance=1,
        )
        self.selection = SimpleNamespace(
            id=self.selection_id,
            case_id=self.case_id,
            run_id=uuid4(),
            scenario_id="scenario-1",
            profile_revision=3,
            settlement_revision=5,
            scenario_result_json=self.result.model_dump(mode="json"),
        )
        self.attempt = SimpleNamespace(
            id=uuid4(),
            attempt_ordinal=1,
            revision=4,
            proposal_issued_at=None,
            proposal_terms_json=None,
            proposal_scenario_result_json=None,
            proposal_version_ordinal=0,
            proposal_draft_unlocked=False,
            snapshot_json={"revisions": {"profile": 3, "settlement": 5}, "settlement_ledger": []},
            editable_state_json={
                "proposed_values": [{"asset_id": str(uuid4()), "proposed_amount_cents": 100}],
                "offer_to": "Party B",
            },
            frozen_at=None,
            sent_confirmed_at=None,
            finalized_at=None,
            finalized_snapshot_json=None,
            finalized_version_ordinal=None,
            finalized_by_user_id_snapshot=None,
        )
        self.settings = SimpleNamespace(
            auth_enabled=True,
            case_data_enabled=True,
            demo_mode_enabled=False,
            max_upload_bytes=2_000_000,
        )
        self.membership = SimpleNamespace(role="owner")
        self.db = Mock()
        self.db.scalar.side_effect = [
            self.membership, self.case, self.selection, self.attempt, None, self.user,
        ]
        self.patches = [
            patch("app.settlement_routes.get_settings", return_value=self.settings),
            patch("app.settlement_routes.render_mediation_offer_docx", return_value=b"docx"),
            patch("app.settlement_routes.render_property_schedule_xlsx", return_value=b"xlsx"),
        ]
        self.render_docx = self.patches[1].start()
        self.patches[0].start()
        self.render_xlsx = self.patches[2].start()
        self.addCleanup(patch.stopall)

    def _final(self, route=create_settlement_offer, **overrides):
        payload = {
            "terms": self.terms,
            "confirm_credit_use": True,
            "finalize": True,
            "confirm_finalization": True,
        }
        payload.update(overrides)
        return route(self.case_id, self.selection_id, OfferCreate(**payload), self.user, self.db)

    def _added(self, kind):
        return [c.args[0] for c in self.db.add.call_args_list if c.args and isinstance(c.args[0], kind)]

    def test_confirmation_is_required_and_changes_nothing(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            self._final(confirm_finalization=False)
        self.assertEqual(raised.exception.status_code, 428)
        self.render_docx.assert_not_called()
        self.assertIsNone(self.attempt.finalized_at)
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.assertFalse(self.case.first_finalization_used)
        self.db.commit.assert_not_called()

    def test_confirmation_without_finalize_is_rejected_by_the_schema(self) -> None:
        with self.assertRaises(ValidationError):
            OfferCreate(terms=self.terms, confirm_finalization=True)

    def test_draft_download_does_not_finalize(self) -> None:
        create_settlement_offer(
            self.case_id,
            self.selection_id,
            OfferCreate(terms=self.terms, confirm_credit_use=True),
            self.user,
            self.db,
        )
        self.assertIsNone(self.attempt.finalized_at)
        self.assertIsNone(self.attempt.finalized_snapshot_json)

    def test_successful_first_final_download_is_free_and_snapshots_once(self) -> None:
        response = self._final()
        self.assertEqual(response.body, b"docx")
        self.assertIsNotNone(self.attempt.finalized_at)
        self.assertEqual(self.attempt.finalized_version_ordinal, 1)
        self.assertEqual(self.attempt.finalized_by_user_id_snapshot, self.user.id)
        self.assertEqual(self.attempt.revision, 5)
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.assertTrue(self.case.first_finalization_used)
        self.assertEqual(len(self._added(DocumentCreditLedgerEntry)), 0)
        self.assertEqual(len(self._added(SettlementProposalVersion)), 1)
        self.db.commit.assert_called_once()
        snapshot = self.attempt.finalized_snapshot_json
        self.assertEqual(snapshot["negotiation"], self.attempt.editable_state_json)
        self.assertEqual(snapshot["proposal_terms"], self.terms.model_dump(mode="json"))
        self.assertEqual(snapshot["scenario"]["result"], self.result.model_dump(mode="json"))
        self.assertEqual(snapshot["revisions"], {"profile": 3, "settlement": 5})
        self.assertEqual(snapshot["proposal_version"]["docx_sha256"], hashlib.sha256(b"docx").hexdigest())
        self.assertEqual(snapshot["proposal_version"]["xlsx_sha256"], hashlib.sha256(b"xlsx").hexdigest())
        self.assertEqual(snapshot["proposal_version"]["ordinal"], 1)
        self.assertEqual(snapshot["entitlement_charge"]["policy"], "free_first_case_finalization")
        self.assertEqual(snapshot["entitlement_charge"]["credit_cost"], 0)
        self.assertIs(snapshot["externally_sent"], False)
        self.assertEqual(snapshot["finalized_by_user_id_snapshot"], str(self.user.id))
        self.assertIsNone(self.attempt.sent_confirmed_at)
        self.assertIsNone(self.attempt.frozen_at)

    def test_snapshot_is_independent_of_later_mutation_of_editable_state(self) -> None:
        self._final()
        self.attempt.editable_state_json["offer_to"] = "tampered"
        self.assertEqual(self.attempt.finalized_snapshot_json["negotiation"]["offer_to"], "Party B")

    def test_legacy_generated_version_does_not_exempt_later_finalization_credit(self) -> None:
        create_settlement_offer(
            self.case_id,
            self.selection_id,
            OfferCreate(terms=self.terms, confirm_credit_use=True),
            self.user,
            self.db,
        )
        version = self._added(SettlementProposalVersion)[0]
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.assertEqual(version.credit_cost, 0)
        self.case.first_finalization_used = True
        self.db.reset_mock()
        self.db.scalar.side_effect = [
            self.membership,
            self.case,
            self.selection,
            self.attempt,
            version,
            None,
        ]
        self.render_docx.reset_mock()
        response = self._final(route=create_settlement_property_schedule, confirm_credit_use=False)
        self.assertEqual(response.body, b"xlsx")
        self.assertIsNotNone(self.attempt.finalized_at)
        self.assertEqual(self.case.attempt_credit_balance, 0)
        self.assertEqual(len(self._added(DocumentCreditLedgerEntry)), 1)
        self.assertEqual(self._added(SettlementProposalVersion), [])
        self.render_docx.assert_not_called()
        self.assertEqual(
            self.attempt.finalized_snapshot_json["entitlement_charge"]["policy"],
            "attempt_credit",
        )

    def test_repeated_finalization_is_idempotent_and_free(self) -> None:
        self._final()
        snapshot = self.attempt.finalized_snapshot_json
        finalized_at = self.attempt.finalized_at
        revision = self.attempt.revision
        version = self._added(SettlementProposalVersion)[0]
        self.db.reset_mock()
        self.render_docx.reset_mock()
        for route in (create_settlement_offer, create_settlement_property_schedule):
            self.db.scalar.side_effect = [self.membership, self.case, self.selection, self.attempt, version]
            self._final(route=route, confirm_credit_use=False)
        self.assertIs(self.attempt.finalized_snapshot_json, snapshot)
        self.assertEqual(self.attempt.finalized_at, finalized_at)
        self.assertEqual(self.attempt.revision, revision)
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.db.add.assert_not_called()
        self.db.commit.assert_called_once()
        self.render_docx.assert_not_called()

    def test_repeat_without_confirmation_is_free_and_plain_redownload_works(self) -> None:
        self._final()
        version = self._added(SettlementProposalVersion)[0]
        self.db.scalar.side_effect = [self.membership, self.case, self.selection, self.attempt, version]
        response = create_settlement_offer(
            self.case_id, self.selection_id, OfferCreate(terms=self.terms), self.user, self.db
        )
        self.assertEqual(response.body, b"docx")
        self.assertEqual(self.case.attempt_credit_balance, 1)

    def test_finalized_attempt_rejects_generation_with_different_terms(self) -> None:
        self._final()
        version = self._added(SettlementProposalVersion)[0]
        self.db.scalar.side_effect = [self.membership, self.case, self.selection, self.attempt, version]
        changed = self.terms.model_copy(update={"offer_to": "Someone else"})
        with self.assertRaises(HTTPException) as raised:
            self._final(terms=changed)
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(self.attempt.finalized_snapshot_json["proposal_terms"]["offer_to"], "Party B")

    def test_finalized_attempt_without_its_version_fails_closed(self) -> None:
        self.attempt.finalized_at = datetime.now(UTC)
        self.attempt.proposal_issued_at = datetime.now(UTC)
        self.attempt.proposal_version_ordinal = 1
        self.attempt.finalized_version_ordinal = 1
        self.db.scalar.side_effect = [self.membership, self.case, self.selection, self.attempt, None]
        with self.assertRaises(HTTPException) as raised:
            self._final()
        self.assertEqual(raised.exception.status_code, 409)
        self.render_docx.assert_not_called()

    def test_render_failure_leaves_attempt_editable_and_uncharged(self) -> None:
        self.render_docx.side_effect = ValueError("render failed")
        with self.assertRaises(HTTPException) as raised:
            self._final()
        self.assertEqual(raised.exception.status_code, 422)
        self.assertIsNone(self.attempt.finalized_at)
        self.assertIsNone(self.attempt.finalized_snapshot_json)
        self.assertIsNone(self.attempt.proposal_issued_at)
        self.assertEqual(self.attempt.revision, 4)
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_unexpected_render_failure_is_safe_and_leaves_attempt_editable(self) -> None:
        self.render_docx.side_effect = RuntimeError("private source content")
        with self.assertRaises(HTTPException) as raised:
            self._final()
        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("saved attempt is unchanged", raised.exception.detail)
        self.assertIsNone(self.attempt.finalized_at)
        self.assertEqual(self.case.attempt_credit_balance, 1)
        self.db.add.assert_not_called()
        self.db.commit.assert_not_called()

    def test_persistence_failure_rolls_back_debit_and_finalization(self) -> None:
        self.db.commit.side_effect = SQLAlchemyError("write failed")
        with self.assertRaises(HTTPException) as raised:
            self._final()
        self.assertEqual(raised.exception.status_code, 503)
        self.db.rollback.assert_called()
        self.assertEqual(self.db.commit.call_count, 1)

    def test_insufficient_balance_does_not_finalize(self) -> None:
        self.case.first_finalization_used = True
        self.case.attempt_credit_balance = 0
        with self.assertRaises(HTTPException) as raised:
            self._final()
        self.assertEqual(raised.exception.status_code, 402)
        self.assertIsNone(self.attempt.finalized_at)
        self.render_docx.assert_not_called()
        self.assertTrue(self.case.first_finalization_used)
        self.assertEqual(self.case.attempt_credit_balance, 0)

    def test_stale_case_revisions_do_not_finalize_an_existing_version(self) -> None:
        create_settlement_offer(
            self.case_id,
            self.selection_id,
            OfferCreate(terms=self.terms, confirm_credit_use=True),
            self.user,
            self.db,
        )
        version = self._added(SettlementProposalVersion)[0]
        self.case.profile_revision += 1
        self.db.scalar.side_effect = [self.membership, self.case, self.selection, self.attempt, version]
        with self.assertRaises(HTTPException) as raised:
            self._final(confirm_credit_use=False)
        self.assertEqual(raised.exception.status_code, 409)
        self.assertIsNone(self.attempt.finalized_at)


class FinalizedAttemptImmutabilityTests(unittest.TestCase):
    def _finalized_attempt(self, **overrides):
        state = OfferAttemptStateUpdate(expected_revision=0).model_dump(
            mode="json", exclude={"expected_revision"}
        )
        values = {
            "attempt_ordinal": 1,
            "frozen_at": None,
            "sent_confirmed_at": None,
            "proposal_issued_at": object(),
            "proposal_draft_unlocked": False,
            "proposal_version_ordinal": 1,
            "finalized_at": object(),
            "revision": 6,
            "snapshot_json": {"revisions": {"profile": 1, "settlement": 2}},
            "editable_state_json": state,
        }
        values.update(overrides)
        return SimpleNamespace(**values)

    def _update(self, attempt, payload):
        case_id = uuid4()
        selection = SimpleNamespace(id=uuid4(), case_id=case_id, scenario_result_json={})
        db = Mock()
        with (
            patch("app.offer_response._authorized_selection"),
            patch(
                "app.offer_response._lock_case",
                return_value=SimpleNamespace(profile_revision=1, settlement_revision=2),
            ),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
            patch("app.offer_response._response_record", return_value=object()),
        ):
            try:
                return update_offer_attempt_state(
                    case_id, selection.id, payload, Response(), SimpleNamespace(id=uuid4()), db
                ), db
            except HTTPException as error:
                return error, db

    def test_content_edits_are_rejected_even_if_a_draft_flag_were_set(self) -> None:
        for unlocked in (False, True):
            attempt = self._finalized_attempt(proposal_draft_unlocked=unlocked)
            error, db = self._update(
                attempt, OfferAttemptStateUpdate(expected_revision=6, offer_to="Changed")
            )
            self.assertIsInstance(error, HTTPException)
            self.assertEqual(error.status_code, 409)
            self.assertIn("finalized", error.detail)
            db.commit.assert_not_called()
            self.assertEqual(attempt.editable_state_json["offer_to"], "")

    def test_scenario_recalculation_is_rejected_after_finalization(self) -> None:
        attempt = self._finalized_attempt()
        axes = ScenarioAxes(
            relationship_windows=[
                RelationshipWindow(
                    id="m",
                    label="Marriage",
                    relationship_type="marriage_only",
                    start_date="2020-01-01",
                    separation_date="2024-01-01",
                )
            ],
            tracing_methods=["explicit"],
            community_share_bps=[5_000],
        )
        error, db = self._update(
            attempt, OfferAttemptStateUpdate(expected_revision=6, scenario_assumptions=axes)
        )
        self.assertEqual(error.status_code, 409)
        db.commit.assert_not_called()

    def test_unchanged_content_resave_is_still_allowed_for_workflow_fields(self) -> None:
        attempt = self._finalized_attempt()
        result, db = self._update(
            attempt, OfferAttemptStateUpdate(expected_revision=6, sent_offer_mode="modified")
        )
        self.assertNotIsInstance(result, HTTPException)
        self.assertEqual(attempt.editable_state_json["sent_offer_mode"], "modified")
        db.commit.assert_called_once()

    def test_new_proposal_version_is_rejected_after_finalization(self) -> None:
        attempt = self._finalized_attempt()
        selection = SimpleNamespace(id=uuid4(), case_id=uuid4())
        db = Mock()
        with (
            patch("app.offer_response._authorized_selection"),
            patch("app.offer_response._lock_case"),
            patch("app.offer_response._selection", return_value=selection),
            patch("app.offer_response._attempt_for_selection", return_value=attempt),
        ):
            with self.assertRaises(HTTPException) as raised:
                start_new_proposal_version(
                    selection.case_id, selection.id, Response(), SimpleNamespace(id=uuid4()), db
                )
        self.assertEqual(raised.exception.status_code, 409)
        self.assertFalse(attempt.proposal_draft_unlocked)
        db.commit.assert_not_called()


class FinalizationReadModelTests(unittest.TestCase):
    def test_read_model_reports_finalization_without_claiming_it_was_sent(self) -> None:
        from app.models import SettlementScenarioSelection
        from app.offer_response import _read_response

        selection = SettlementScenarioSelection(
            id=uuid4(),
            case_id=uuid4(),
            user_id_snapshot=uuid4(),
            idempotency_key=uuid4(),
            request_sha256="test",
            run_id=uuid4(),
            scenario_id="s",
            scenario_result_json={"scenario": {"id": "s"}},
            profile_revision=0,
            settlement_revision=0,
        )
        finalized_at = datetime.now(UTC)
        attempt = SimpleNamespace(
            id=uuid4(),
            attempt_ordinal=1,
            frozen_at=None,
            sent_confirmed_at=None,
            revision=3,
            editable_state_json={},
            snapshot_json={},
            frozen_snapshot_json=None,
            proposal_issued_at=finalized_at,
            proposal_terms_json=None,
            proposal_scenario_result_json=None,
            finalized_at=finalized_at,
            finalized_version_ordinal=2,
        )
        db = Mock()
        db.scalar.side_effect = [attempt, None, None]
        result = _read_response(db, selection, None)
        self.assertTrue(result.finalized)
        self.assertEqual(result.finalized_at, finalized_at)
        self.assertEqual(result.finalized_version_ordinal, 2)
        self.assertIsNone(result.attempt_limit)
        self.assertIsNone(result.attempts_remaining)
        self.assertFalse(result.sent_confirmed)
        self.assertFalse(result.frozen)

    def test_sent_confirmation_snapshot_references_the_finalization(self) -> None:
        from app.offer_response import _frozen_attempt_snapshot

        finalized_at = datetime.now(UTC)
        attempt = SimpleNamespace(
            snapshot_json={"scenario": {"objective": "o"}},
            editable_state_json={},
            finalized_at=finalized_at,
            finalized_version_ordinal=2,
            finalized_snapshot_json={"snapshot_sha256": "abc"},
        )
        selection = SimpleNamespace(run_id=uuid4(), scenario_id="s", scenario_result_json={})
        snapshot = _frozen_attempt_snapshot(
            attempt,
            selection,
            SimpleNamespace(attachments=[]),
            confirmed_at=datetime.now(UTC),
            user_id=uuid4(),
        )
        self.assertEqual(snapshot["finalization"]["version_ordinal"], 2)
        self.assertEqual(snapshot["finalization"]["snapshot_sha256"], "abc")




class FinalizationModelTests(unittest.TestCase):
    def test_attempt_model_has_nullable_finalization_columns(self) -> None:
        table = SettlementNegotiationAttempt.__table__
        for name in (
            "finalized_at",
            "finalized_snapshot_json",
            "finalized_version_ordinal",
            "finalized_by_user_id_snapshot",
        ):
            self.assertIn(name, table.c)
            self.assertTrue(table.c[name].nullable)


if __name__ == "__main__":
    unittest.main()
