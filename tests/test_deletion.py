import unittest
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from fastapi import HTTPException
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.case_limits import require_active_case_slot
from app.deletion import (
    ACCOUNT_CONFIRMATION,
    CASE_CONFIRMATION,
    MATERIAL_CONFIRMATION,
    AccountDeletionRequest,
    PermanentDeletionConfirmation,
    delete_account_scope,
    delete_case_scope,
    delete_document_scope,
    import_item_tombstone_id,
    router,
)
from app.models import (
    Case,
    CaseDelegationInvitation,
    CaseLifecycleEvent,
    CaseMembership,
    DeletionTombstone,
    Document,
    DocumentExtraction,
    MaterialImportBatch,
    MaterialImportItem,
    NegotiationEvent,
    User,
)


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


class FakeStorage:
    def __init__(self) -> None:
        self.deleted: list[str] = []
        self.fail = False

    def delete_all_versions(self, key: str) -> None:
        if self.fail:
            raise RuntimeError("object version purge failed")
        self.deleted.append(key)


class PermanentDeletionTests(unittest.TestCase):
    def setUp(self) -> None:
        self._defaults = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                default = column.server_default
                if default is not None and "::" in str(getattr(default, "arg", "")):
                    self._defaults.append((column, default))
                    column.server_default = None
        self.engine = create_engine(
            "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        event.listen(self.engine, "connect", self._enable_foreign_keys)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, expire_on_commit=False)
        self.storage = FakeStorage()
        self.owner = User(email="owner@example.com", status="active", password_hash="hash")
        self.viewer = User(email="viewer@example.com", status="active", password_hash="hash")
        self.case = Case(status="settlement", metadata_json={"sensitive": "case data"})
        self.db.add_all([self.owner, self.viewer, self.case])
        self.db.flush()
        self.db.add_all(
            [
                CaseMembership(case_id=self.case.id, user_id=self.owner.id, role="owner"),
                CaseMembership(case_id=self.case.id, user_id=self.viewer.id, role="viewer"),
                CaseLifecycleEvent(
                    case_id=self.case.id,
                    user_id_snapshot=self.owner.id,
                    event_type="closed",
                ),
                NegotiationEvent(
                    case_id=self.case.id,
                    event_type="note",
                    payload={"sensitive": "derived case data"},
                ),
            ]
        )
        self.document = Document(
            case_id=self.case.id,
            object_key=f"{self.case.id}/source.pdf",
            extension="pdf",
            media_type="application/pdf",
            sha256="0" * 64,
            size_bytes=10,
        )
        self.batch_id = uuid4()
        self.item_id = uuid4()
        self.db.add(self.document)
        self.db.flush()
        self.db.add(
            DocumentExtraction(
                document_id=self.document.id,
                extracted_text="derived text",
                page_count=1,
                pages_json=[{"page_number": 1, "text": "derived text"}],
            )
        )
        self.db.add_all(
            [
                MaterialImportBatch(
                    id=self.batch_id,
                    user_id=self.owner.id,
                    case_id=self.case.id,
                ),
                MaterialImportItem(
                    batch_id=self.batch_id,
                    item_id=self.item_id,
                    document_id=self.document.id,
                ),
            ]
        )
        self.db.commit()

    @staticmethod
    def _enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        for column, default in self._defaults:
            column.server_default = default

    def test_deletion_routes_require_distinct_confirmation_phrases(self) -> None:
        paths = {route.path for route in router.routes}
        self.assertIn("/cases/{case_id}/permanent-deletion", paths)
        self.assertIn(
            "/cases/{case_id}/materials/{document_id}/permanent-deletion", paths
        )
        self.assertIn("/api/v1/account/permanent-deletion", paths)
        self.assertEqual(
            PermanentDeletionConfirmation(confirmation=CASE_CONFIRMATION).confirmation,
            CASE_CONFIRMATION,
        )
        self.assertEqual(
            PermanentDeletionConfirmation(
                confirmation=MATERIAL_CONFIRMATION
            ).confirmation,
            MATERIAL_CONFIRMATION,
        )
        self.assertEqual(
            AccountDeletionRequest(
                confirmation=ACCOUNT_CONFIRMATION,
                password="verified",
            ).confirmation,
            ACCOUNT_CONFIRMATION,
        )

    def test_account_creation_barrier_blocks_disabled_or_tombstoned_accounts(self) -> None:
        self.owner.status = "disabled"
        with self.assertRaises(HTTPException) as disabled:
            require_active_case_slot(self.db, self.owner.id)
        self.assertEqual(disabled.exception.status_code, 410)

        self.owner.status = "active"
        self.db.add(
            DeletionTombstone(
                scope_type="account",
                scope_id=self.owner.id,
                initiated_by=self.owner.id,
                status="pending",
                object_keys=[],
            )
        )
        self.db.commit()
        with self.assertRaises(HTTPException) as pending:
            require_active_case_slot(self.db, self.owner.id)
        self.assertEqual(pending.exception.status_code, 410)

    def test_material_deletion_removes_source_and_derived_data_and_leaves_tombstone(self) -> None:
        deleted = delete_document_scope(self.db, self.owner, self.case.id, self.document.id, self.storage)

        self.assertTrue(deleted)
        self.assertIsNone(self.db.get(Document, self.document.id))
        self.assertEqual(self.db.scalar(select(DocumentExtraction.id)), None)
        tombstone = self.db.scalar(
            select(DeletionTombstone).where(
                DeletionTombstone.scope_type == "document",
                DeletionTombstone.scope_id == self.document.id,
            )
        )
        self.assertEqual(tombstone.status, "completed")
        self.assertEqual(tombstone.object_keys, [])
        self.assertEqual(self.storage.deleted, [self.document.object_key])
        self.assertEqual(
            self.db.scalar(
                select(DeletionTombstone.status).where(
                    DeletionTombstone.scope_type == "import_item",
                    DeletionTombstone.scope_id
                    == import_item_tombstone_id(self.batch_id, self.item_id),
                )
            ),
            "completed",
        )

    def test_case_deletion_removes_case_rows_documents_and_every_known_object(self) -> None:
        deleted = delete_case_scope(self.db, self.owner, self.case.id, self.storage)

        self.assertTrue(deleted)
        self.assertIsNone(self.db.get(Case, self.case.id))
        self.assertEqual(self.db.scalar(select(DocumentExtraction.id)), None)
        self.assertEqual(self.db.scalar(select(NegotiationEvent.id)), None)
        self.assertEqual(self.db.scalar(select(CaseLifecycleEvent.id)), None)
        self.assertEqual(self.storage.deleted, [self.document.object_key])
        self.assertTrue(
            self.db.scalar(
                select(DeletionTombstone.id).where(
                    DeletionTombstone.scope_type == "case",
                    DeletionTombstone.scope_id == self.case.id,
                    DeletionTombstone.status == "completed",
                )
            )
        )

    def test_case_deletion_is_idempotent_for_confirming_owner(self) -> None:
        delete_case_scope(self.db, self.owner, self.case.id, self.storage)
        self.assertTrue(delete_case_scope(self.db, self.owner, self.case.id, self.storage))
        self.assertEqual(self.storage.deleted, [self.document.object_key])

    def test_non_owner_cannot_delete_material_or_case(self) -> None:
        for delete in (
            lambda: delete_document_scope(
                self.db, self.viewer, self.case.id, self.document.id, self.storage
            ),
            lambda: delete_case_scope(self.db, self.viewer, self.case.id, self.storage),
        ):
            with self.assertRaises(HTTPException) as raised:
                delete()
            self.assertEqual(raised.exception.status_code, 403)
        self.assertEqual(self.storage.deleted, [])
        self.assertEqual(self.db.scalar(select(DeletionTombstone.id)), None)

    def test_object_failure_leaves_pending_tombstone_and_retry_finishes(self) -> None:
        self.storage.fail = True
        with self.assertRaises(HTTPException) as raised:
            delete_case_scope(self.db, self.owner, self.case.id, self.storage)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertIsNotNone(self.db.get(Case, self.case.id))
        tombstone = self.db.scalar(
            select(DeletionTombstone).where(
                DeletionTombstone.scope_type == "case",
                DeletionTombstone.scope_id == self.case.id,
            )
        )
        self.assertEqual(tombstone.status, "pending")
        self.storage.fail = False

        self.assertTrue(delete_case_scope(self.db, self.owner, self.case.id, self.storage))
        self.assertIsNone(self.db.get(Case, self.case.id))
        self.assertEqual(self.storage.deleted, [self.document.object_key])

    def test_account_deletion_removes_owned_case_and_account_but_not_other_case(self) -> None:
        other_owner = User(email="other@example.com", status="active")
        other_case = Case(status="draft")
        self.db.add_all([other_owner, other_case])
        self.db.flush()
        invitation = CaseDelegationInvitation(
            case_id=other_case.id,
            owner_user_id=other_owner.id,
            invitee_email=self.owner.email,
            token_hash="a" * 64,
            status="accepted",
            delegate_user_id=self.owner.id,
            expires_at=datetime.now(UTC) + timedelta(days=1),
        )
        self.db.add_all(
            [
                CaseMembership(case_id=other_case.id, user_id=other_owner.id, role="owner"),
                CaseMembership(case_id=other_case.id, user_id=self.owner.id, role="viewer"),
                CaseLifecycleEvent(
                    case_id=other_case.id,
                    user_id_snapshot=self.owner.id,
                    event_type="reopened",
                ),
            ]
        )
        self.db.add(invitation)
        self.db.commit()

        self.assertTrue(delete_account_scope(self.db, self.owner, self.storage))

        self.assertIsNone(self.db.get(User, self.owner.id))
        self.assertIsNone(self.db.get(Case, self.case.id))
        self.assertIsNotNone(self.db.get(Case, other_case.id))
        self.assertIsNone(
            self.db.scalar(
                select(CaseMembership.id).where(
                    CaseMembership.case_id == other_case.id,
                    CaseMembership.user_id == self.owner.id,
                )
            )
        )
        self.assertEqual(self.storage.deleted, [self.document.object_key])
        retained_actor_id = self.db.scalar(
            select(CaseLifecycleEvent.user_id_snapshot).where(
                CaseLifecycleEvent.case_id == other_case.id
            )
        )
        self.assertNotEqual(retained_actor_id, self.owner.id)
        self.db.refresh(invitation)
        self.assertEqual(invitation.invitee_email, f"deleted-{self.owner.id}@invalid.invalid")
        self.assertEqual(invitation.status, "revoked")
        self.assertIsNotNone(invitation.revoked_at)
        self.assertEqual(
            self.db.scalar(
                select(DeletionTombstone.status).where(
                    DeletionTombstone.scope_type == "account",
                    DeletionTombstone.scope_id == self.owner.id,
                )
            ),
            "completed",
        )

    def test_account_deletion_failure_keeps_retryable_barrier(self) -> None:
        self.storage.fail = True
        with self.assertRaises(HTTPException) as raised:
            delete_account_scope(self.db, self.owner, self.storage)
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(self.db.get(User, self.owner.id).status, "disabled")
        self.assertIsNotNone(self.db.get(Case, self.case.id))
        self.assertEqual(
            self.db.scalar(
                select(DeletionTombstone.status).where(
                    DeletionTombstone.scope_type == "account",
                    DeletionTombstone.scope_id == self.owner.id,
                )
            ),
            "pending",
        )

        self.storage.fail = False
        self.assertTrue(delete_account_scope(self.db, self.owner, self.storage))
        self.assertIsNone(self.db.get(User, self.owner.id))
        self.assertIsNone(self.db.get(Case, self.case.id))


if __name__ == "__main__":
    unittest.main()
