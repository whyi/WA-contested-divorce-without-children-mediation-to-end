import io
import json
import unittest
from uuid import uuid4
from zipfile import ZipFile

from fastapi import HTTPException
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.case_lifecycle import (
    CaseCloseRequest,
    close_case,
    export_case,
    lifecycle_write_allowed,
    list_closed_cases,
    require_attempts_editable,
    reopen_case,
)
from app.database import Base
from app.models import (
    Case,
    CaseLifecycleEvent,
    CaseMembership,
    Document,
    DocumentCreditLedgerEntry,
    NegotiationEvent,
    SettlementNegotiationAttempt,
    SettlementProposalVersion,
    SettlementScenarioRun,
    SettlementScenarioSelection,
    User,
)
from app.offer_response import _finalize_case_record


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


class FakeStorage:
    def __init__(self) -> None:
        self.objects = {"case/doc.pdf": b"%PDF-user-file"}
        self.deleted: list[str] = []

    def get(self, key: str) -> bytes:
        return self.objects[key]

    def delete(self, key: str) -> None:
        self.deleted.append(key)


class LifecycleFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._defaults = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                default = column.server_default
                if default is not None and "::" in str(getattr(default, "arg", "")):
                    self._defaults.append((column, default))
                    column.server_default = None
        engine = create_engine(
            "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.storage = FakeStorage()
        self.user = User(email="owner@example.com", password_hash="secret-hash", status="active")
        self.other = User(email="other@example.com", status="active")
        self.viewer = User(email="viewer@example.com", status="active")
        self.db.add_all([self.user, self.other, self.viewer])
        self.db.flush()
        self.case = Case(
            status="settlement",
            metadata_json={"case_title": "Mine", "initial_offer": {"amount": 5}},
            wizard_intake_json={"schema_version": 1, "filed": "yes", "role": "petitioner"},
            wizard_intake_revision=2,
            attempt_credit_balance=3,
        )
        self.db.add(self.case)
        self.db.flush()
        self.db.add_all(
            [
                CaseMembership(case_id=self.case.id, user_id=self.user.id, role="owner"),
                CaseMembership(case_id=self.case.id, user_id=self.viewer.id, role="viewer"),
                NegotiationEvent(case_id=self.case.id, event_type="note", payload={"t": "hi"}),
                Document(
                    case_id=self.case.id,
                    object_key="case/doc.pdf",
                    extension="pdf",
                    media_type="application/pdf",
                    sha256="0" * 64,
                    size_bytes=14,
                ),
            ]
        )
        run = SettlementScenarioRun(
            case_id=self.case.id,
            user_id_snapshot=self.user.id,
            profile_revision=0,
            settlement_revision=0,
            objective="x",
            axes_json={},
            scenario_results_json=[],
        )
        self.db.add(run)
        self.db.flush()
        selection = SettlementScenarioSelection(
            case_id=self.case.id,
            user_id_snapshot=self.user.id,
            idempotency_key=uuid4(),
            request_sha256="0" * 64,
            run_id=run.id,
            scenario_id="a",
            scenario_result_json={},
            profile_revision=0,
            settlement_revision=0,
        )
        self.db.add(selection)
        self.db.flush()
        self.attempt = SettlementNegotiationAttempt(
            case_id=self.case.id,
            selection_id=selection.id,
            attempt_ordinal=1,
            snapshot_json={"snap": 1},
            proposal_terms_json={"offer": 42},
        )
        self.db.add(self.attempt)
        self.db.flush()
        self.version = SettlementProposalVersion(
            case_id=self.case.id,
            attempt_id=self.attempt.id,
            user_id_snapshot=self.user.id,
            version_ordinal=1,
            request_sha256="0" * 64,
            terms_json={},
            scenario_result_json={},
            docx_content=b"DOCX-BYTES",
            xlsx_content=b"XLSX-BYTES",
            credit_cost=1,
        )
        self.db.add(self.version)
        self.db.flush()
        self.db.add(
            DocumentCreditLedgerEntry(
                user_id=self.user.id,
                case_id=self.case.id,
                proposal_version_id=self.version.id,
                source_type="legacy_document_credit",
                idempotency_key="l1",
                delta=-1,
                balance_after=3,
            )
        )
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        for column, default in self._defaults:
            column.server_default = default


class CloseAndReopenTests(LifecycleFixture):
    def test_reopen_resumes_only_current_stopped_mediation(self) -> None:
        self.attempt.attempt_ordinal = 3
        current = {
            "revision": 7, "stopped": True, "sent": True, "outcome": "rejected",
            "notes": "Preserve response", "document_ids": [],
        }
        historical = {"revision": 2, "stopped": True, "sent": True}
        self.case.metadata_json = {
            **self.case.metadata_json,
            "asset_mediation": {"1": historical, "3": current},
        }
        self.db.commit()
        close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        reopen_case(self.case.id, self.user, self.db)
        self.db.refresh(self.case)
        saved = self.case.metadata_json["asset_mediation"]
        self.assertEqual(saved["3"], {**current, "stopped": False, "revision": 8})
        self.assertEqual(saved["1"], historical)
        self.assertEqual(self.attempt.snapshot_json, {"snap": 1})
        self.assertEqual(self.case.attempt_credit_balance, 3)
        self.assertEqual(self.db.query(SettlementNegotiationAttempt).count(), 1)

    def test_reopen_preserves_nonstopped_mediation(self) -> None:
        saved = {"1": {"revision": 4, "stopped": False, "completed": True}}
        self.case.metadata_json = {**self.case.metadata_json, "asset_mediation": saved}
        self.db.commit()
        close_case(self.case.id, CaseCloseRequest(), self.user, self.db)
        reopen_case(self.case.id, self.user, self.db)
        self.assertEqual(self.case.metadata_json["asset_mediation"], saved)

    def test_close_then_reopen_preserves_case_attempts_files_and_credits(self) -> None:
        close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        self.db.refresh(self.case)
        self.assertIsNotNone(self.case.closed_at)
        self.assertEqual(self.case.closed_reason, "stopped")
        self.assertEqual(self.case.status, "settlement")
        reopen_case(self.case.id, self.user, self.db)
        self.db.refresh(self.case)
        self.assertIsNone(self.case.closed_at)
        self.assertEqual(self.case.status, "settlement")
        self.assertEqual(self.case.attempt_credit_balance, 3)
        self.assertEqual(self.db.query(Case).count(), 1)
        self.assertEqual(self.db.query(SettlementNegotiationAttempt).count(), 1)
        self.assertEqual(self.db.query(SettlementProposalVersion).count(), 1)
        self.assertEqual(self.db.query(Document).count(), 1)
        self.assertEqual(self.storage.deleted, [])
        events = self.db.scalars(
            select(CaseLifecycleEvent.event_type).order_by(CaseLifecycleEvent.created_at)
        ).all()
        self.assertCountEqual(events, ["closed", "reopened"])

    def test_rejected_closure_preserves_response_and_does_not_add_accepted_lock(self) -> None:
        response = {
            "revision": 4, "outcome": "rejected", "sent": True,
            "stopped": False, "notes": "Retained response", "document_ids": [],
        }
        self.case.metadata_json = {**self.case.metadata_json, "asset_mediation": {"1": response}}
        self.db.commit()
        result = close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        self.assertEqual(result.id, self.case.id)
        self.assertIsNotNone(result.closed_at)
        self.assertEqual(result.closed_reason, "stopped")
        self.assertEqual(result.status, "settlement")
        self.assertIsNone(self.case.attempts_locked_at)
        reopen_case(self.case.id, self.user, self.db)
        self.db.refresh(self.case)
        self.assertEqual(self.case.metadata_json["asset_mediation"]["1"], response)
        self.assertIsNone(self.case.attempts_locked_at)
        self.assertEqual(self.case.attempt_credit_balance, 3)
        self.assertEqual(self.storage.deleted, [])

    def test_close_has_no_expiry_or_deletion_fields_and_is_idempotent(self) -> None:
        close_case(self.case.id, CaseCloseRequest(reason="closed"), self.user, self.db)
        first = self.db.get(Case, self.case.id).closed_at
        close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        case = self.db.get(Case, self.case.id)
        self.assertEqual(case.closed_at, first)
        self.assertEqual(case.closed_reason, "closed")
        self.assertFalse(
            [c for c in Case.__table__.columns.keys() if "expire" in c or "purge" in c]
        )
        self.assertEqual(self.db.query(CaseLifecycleEvent).count(), 1)

    def test_accepted_completion_is_reopenable_and_restores_prior_status(self) -> None:
        _finalize_case_record(self.case, self.user.id, self.db)
        self.db.commit()
        self.assertEqual(self.case.status, "finalized")
        self.assertEqual(self.case.closed_reason, "accepted")
        self.assertIsNotNone(self.case.attempts_locked_at)
        reopen_case(self.case.id, self.user, self.db)
        self.db.refresh(self.case)
        self.assertEqual(self.case.status, "settlement")
        self.assertIsNone(self.case.closed_at)
        self.assertIsNotNone(self.case.attempts_locked_at)
        with self.assertRaises(HTTPException) as caught:
            require_attempts_editable(self.case)
        self.assertEqual(caught.exception.status_code, 409)

    def test_nonaccepted_closure_does_not_permanently_lock_attempts(self) -> None:
        close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        self.assertIsNone(self.case.attempts_locked_at)

    def test_legacy_finalized_case_reopens_to_settlement(self) -> None:
        self.case.status = "finalized"
        self.db.commit()
        reopen_case(self.case.id, self.user, self.db)
        self.db.refresh(self.case)
        self.assertEqual(self.case.status, "settlement")

    def test_only_owners_can_close_or_reopen(self) -> None:
        for call in (
            lambda: close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.viewer, self.db),
            lambda: reopen_case(self.case.id, self.other, self.db),
        ):
            with self.assertRaises(HTTPException) as caught:
                call()
            self.assertIn(caught.exception.status_code, {403, 404})

    def test_reopen_of_open_case_conflicts(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            reopen_case(self.case.id, self.user, self.db)
        self.assertEqual(caught.exception.status_code, 409)

    def test_reopen_preserves_case_credits_without_tier_entitlements(self) -> None:
        close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        second = Case(status="draft")
        self.db.add(second)
        self.db.flush()
        self.db.add(CaseMembership(case_id=second.id, user_id=self.user.id, role="owner"))
        self.db.commit()
        reopen_case(self.case.id, self.user, self.db)
        self.assertIsNone(self.db.get(Case, self.case.id).closed_at)
        self.assertEqual(self.db.get(Case, self.case.id).status, "settlement")
        self.assertEqual(self.db.get(Case, self.case.id).attempt_credit_balance, 3)

    def test_closed_case_listing_is_owner_scoped(self) -> None:
        close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        listed = list_closed_cases(self.user, self.db)
        self.assertEqual([c.id for c in listed.cases], [self.case.id])
        self.assertEqual(list_closed_cases(self.other, self.db).cases, [])


class ClosedWriteGuardTests(LifecycleFixture):
    def test_closed_and_finalized_cases_block_writes_except_lifecycle_routes(self) -> None:
        base = f"/cases/{self.case.id}"
        self.assertTrue(lifecycle_write_allowed(self.case, f"{base}/documents/render"))
        close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        self.assertFalse(lifecycle_write_allowed(self.case, f"{base}/documents/render"))
        self.assertTrue(lifecycle_write_allowed(self.case, f"{base}/reopen"))
        self.assertTrue(lifecycle_write_allowed(self.case, f"{base}/close"))
        self.assertTrue(lifecycle_write_allowed(self.case, f"{base}/permanent-deletion"))
        self.assertTrue(
            lifecycle_write_allowed(
                self.case, f"{base}/materials/{uuid4()}/permanent-deletion"
            )
        )
        self.case.closed_at = None
        self.case.status = "finalized"
        self.assertFalse(lifecycle_write_allowed(self.case, f"{base}/negotiations"))
        self.assertTrue(lifecycle_write_allowed(self.case, f"{base}/reopen"))
        self.assertTrue(lifecycle_write_allowed(self.case, f"{base}/permanent-deletion"))


class ExportTests(LifecycleFixture):
    def export(self, user=None) -> tuple[ZipFile, dict]:
        response = export_case(self.case.id, user or self.user, self.db, self.storage)
        self.assertEqual(response.headers["cache-control"], "no-store")
        self.assertEqual(response.media_type, "application/zip")
        archive = ZipFile(io.BytesIO(response.body))
        return archive, json.loads(archive.read("manifest.json"))

    def test_export_contains_all_case_data_files_and_credits(self) -> None:
        archive, manifest = self.export()
        names = archive.namelist()
        self.assertIn("README.txt", names)
        self.assertEqual(manifest["case"]["metadata_json"]["initial_offer"], {"amount": 5})
        self.assertEqual(
            manifest["case"]["wizard_intake_json"],
            {"schema_version": 1, "filed": "yes", "role": "petitioner"},
        )
        self.assertEqual(manifest["case"]["wizard_intake_revision"], 2)
        self.assertEqual(manifest["tables"]["settlement_negotiation_attempts"][0]["proposal_terms_json"], {"offer": 42})
        self.assertEqual(manifest["tables"]["negotiation_events"][0]["payload"], {"t": "hi"})
        self.assertEqual(manifest["credits"]["balance"], 3)
        self.assertEqual(len(manifest["credits"]["ledger"]), 1)
        document_path = next(
            f["path"] for f in manifest["files"] if f["kind"] == "document"
        )
        self.assertEqual(archive.read(document_path), b"%PDF-user-file")
        contents = {archive.read(f["path"]) for f in manifest["files"]}
        self.assertIn(b"DOCX-BYTES", contents)
        self.assertIn(b"XLSX-BYTES", contents)

    def test_export_has_no_quota_and_works_for_closed_cases(self) -> None:
        close_case(self.case.id, CaseCloseRequest(reason="stopped"), self.user, self.db)
        for _ in range(3):
            _, manifest = self.export()
        self.assertEqual(manifest["case"]["status"], "settlement")
        self.assertIsNotNone(manifest["case"]["closed_at"])
        self.assertIsNone(manifest["case"]["attempts_locked_at"])
        self.assertEqual(self.db.get(Case, self.case.id).closed_reason, "stopped")

    def test_accepted_case_export_includes_persistent_attempt_lock(self) -> None:
        _finalize_case_record(self.case, self.user.id, self.db)
        self.db.commit()

        _, manifest = self.export()

        self.assertIsNotNone(manifest["case"]["attempts_locked_at"])

    def test_export_minimizes_data_and_is_membership_scoped(self) -> None:
        _, manifest = self.export()
        serialized = json.dumps(manifest)
        for forbidden in (
            "password_hash",
            "secret-hash",
            "other@example.com",
            "owner@example.com",
            "object_key",
            "case/doc.pdf",
            "lease_token",
        ):
            self.assertNotIn(forbidden, serialized)
        self.assertNotIn("case_memberships", manifest["tables"])
        with self.assertRaises(HTTPException) as caught:
            export_case(self.case.id, self.other, self.db, self.storage)
        self.assertEqual(caught.exception.status_code, 404)

    def test_viewer_member_exports_case_balance_without_other_users_ledger(self) -> None:
        _, manifest = self.export(self.viewer)
        self.assertEqual(manifest["credits"]["ledger"], [])
        self.assertEqual(manifest["credits"]["balance"], 3)

    def test_readme_does_not_claim_legal_resolution(self) -> None:
        archive, _ = self.export()
        readme = archive.read("README.txt").decode()
        self.assertIn("not a legal", readme.lower())


if __name__ == "__main__":
    unittest.main()
