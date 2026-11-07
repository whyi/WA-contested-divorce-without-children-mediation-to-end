import unittest

from fastapi import HTTPException
from sqlalchemy import create_engine, event, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.config import Settings
from app.database import Base
from app.models import (
    Case,
    CaseMembership,
    DeletionTombstone,
    Document,
    OwnerBetaFixtureRegistry,
    User,
)
from app.uat_fixtures import (
    RESET_CONFIRMATION,
    reset_owner_beta_case,
    track_owner_beta_fixture_case,
)


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


class FakeStorage:
    def __init__(self) -> None:
        self.checked_ready = False
        self.deleted: list[str] = []
        self.ledger_entries: list[dict[str, object]] = []
        self.fail_deletion = False
        self.fail_ledger = False

    def check_ready(self) -> None:
        self.checked_ready = True

    def record_deletion_tombstone(
        self,
        scope_type: str,
        scope_id: str,
        initiated_by: str,
        object_keys: list[str] | None = None,
    ) -> None:
        if self.fail_ledger:
            raise RuntimeError("ledger unavailable")
        self.ledger_entries.append(
            {
                "scope_type": scope_type,
                "scope_id": scope_id,
                "initiated_by": initiated_by,
                "object_keys": object_keys or [],
            }
        )

    def delete_all_versions(self, key: str) -> None:
        if self.fail_deletion:
            raise RuntimeError("object purge failed")
        self.deleted.append(key)


def owner_beta_settings() -> Settings:
    return Settings(
        auth_enabled=True,
        auth_jwt_secret="secure-test-signing-secret-that-is-long-enough",
        auth_encryption_key="secure-encryption-secret-that-is-long-enough",
        auth_issuer="https://uat.example.test",
        auth_public_base_url="https://uat.example.test",
        webauthn_origin="https://uat.example.test",
        owner_beta_enabled=True,
        owner_beta_email="owner@example.com",
        owner_beta_readiness_required=True,
        owner_beta_fixture_reset_enabled=True,
        owner_beta_fixture_database_host_prefix="casework-owner-beta-uat",
        database_url=(
            "postgresql+psycopg://casework:password@"
            "casework-owner-beta-uat.abc.us-west-2.rds.amazonaws.com:5432/"
            "owner_beta_uat?sslmode=require"
        ),
        s3_bucket="casework-owner-beta-uat-documents-123",
        deletion_ledger_bucket="casework-owner-beta-uat-deletion-ledger-123",
        s3_kms_key_id="arn:aws:kms:us-west-2:123456789012:key/test",
        case_data_enabled=True,
        case_materials_enabled=True,
        smtp_host="email-smtp.us-west-2.amazonaws.com",
        auth_email_from="owner@example.com",
    )


class OwnerBetaFixtureResetTests(unittest.TestCase):
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
        event.listen(self.engine, "connect", self._enable_foreign_keys)
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine, expire_on_commit=False)
        self.settings = owner_beta_settings()
        self.storage = FakeStorage()
        self.owner = User(
            email="owner@example.com",
            status="active",
            account_type="party",
            password_hash="hashed",
        )
        self.db.add(self.owner)
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        self.engine.dispose()
        for column, default in self._server_defaults:
            column.server_default = default

    @staticmethod
    def _enable_foreign_keys(connection, _record) -> None:
        cursor = connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    def _register_case(self) -> Case:
        case = Case(
            status="draft",
            metadata_json={"case_title": "Synthetic UAT"},
        )
        self.db.add(case)
        self.db.flush()
        self.db.add(CaseMembership(case_id=case.id, user_id=self.owner.id, role="owner"))
        self.db.add(
            OwnerBetaFixtureRegistry(owner_user_id=self.owner.id, case_id=case.id)
        )
        self.db.commit()
        return case

    def test_reset_permanently_deletes_registered_case_and_preserves_owner(self) -> None:
        case = self._register_case()
        document = Document(
            case_id=case.id,
            object_key=f"{case.id}/synthetic.pdf",
            extension="pdf",
            media_type="application/pdf",
            sha256="0" * 64,
            size_bytes=12,
        )
        object_key = document.object_key
        self.db.add(document)
        self.db.commit()

        deleted_case_id = reset_owner_beta_case(
            self.db,
            self.settings,
            self.storage,
            RESET_CONFIRMATION,
        )

        self.assertEqual(deleted_case_id, case.id)
        self.assertTrue(self.storage.checked_ready)
        self.assertEqual(self.storage.deleted, [object_key])
        self.assertEqual(len(self.storage.ledger_entries), 1)
        self.assertIsNone(self.db.get(Case, case.id))
        self.assertIsNotNone(self.db.get(User, self.owner.id))
        registry = self.db.get(OwnerBetaFixtureRegistry, self.owner.id)
        self.assertIsNotNone(registry)
        self.assertIsNone(registry.case_id)
        tombstone = self.db.scalar(
            select(DeletionTombstone).where(
                DeletionTombstone.scope_type == "case",
                DeletionTombstone.scope_id == case.id,
            )
        )
        self.assertEqual(tombstone.status, "completed")

    def test_reset_is_idempotent_when_the_clean_baseline_is_active(self) -> None:
        self.db.add(
            OwnerBetaFixtureRegistry(owner_user_id=self.owner.id, case_id=None)
        )
        self.db.commit()

        result = reset_owner_beta_case(
            self.db,
            self.settings,
            self.storage,
            RESET_CONFIRMATION,
        )

        self.assertIsNone(result)
        self.assertTrue(self.storage.checked_ready)
        self.assertEqual(self.storage.ledger_entries, [])

    def test_reset_refuses_unregistered_existing_case(self) -> None:
        case = Case(status="draft", metadata_json={})
        self.db.add(case)
        self.db.flush()
        self.db.add(CaseMembership(case_id=case.id, user_id=self.owner.id, role="owner"))
        self.db.commit()

        with self.assertRaisesRegex(RuntimeError, "not registered as UAT data"):
            reset_owner_beta_case(
                self.db,
                self.settings,
                self.storage,
                RESET_CONFIRMATION,
            )

        self.assertIsNotNone(self.db.get(Case, case.id))
        self.assertEqual(self.storage.ledger_entries, [])

    def test_reset_keeps_registry_and_case_when_object_purge_fails(self) -> None:
        case = self._register_case()
        self.db.add(
            Document(
                case_id=case.id,
                object_key=f"{case.id}/synthetic.pdf",
                extension="pdf",
                media_type="application/pdf",
                sha256="0" * 64,
                size_bytes=12,
            )
        )
        self.db.commit()
        self.storage.fail_deletion = True

        with self.assertRaises(HTTPException):
            reset_owner_beta_case(
                self.db,
                self.settings,
                self.storage,
                RESET_CONFIRMATION,
            )

        self.assertIsNotNone(self.db.get(Case, case.id))
        registry = self.db.get(OwnerBetaFixtureRegistry, self.owner.id)
        self.assertEqual(registry.case_id, case.id)
        tombstone = self.db.scalar(
            select(DeletionTombstone).where(
                DeletionTombstone.scope_type == "case",
                DeletionTombstone.scope_id == case.id,
            )
        )
        self.assertEqual(tombstone.status, "pending")

    def test_reset_keeps_case_when_deletion_ledger_write_fails(self) -> None:
        case = self._register_case()
        self.storage.fail_ledger = True

        with self.assertRaises(HTTPException):
            reset_owner_beta_case(
                self.db,
                self.settings,
                self.storage,
                RESET_CONFIRMATION,
            )

        self.assertIsNotNone(self.db.get(Case, case.id))
        self.assertEqual(self.storage.ledger_entries, [])

    def test_reset_refuses_when_database_or_storage_identity_is_not_uat(self) -> None:
        unsafe_settings = self.settings.model_copy(
            update={"database_url": "postgresql://prod.example.com/owner_beta_uat"}
        )

        with self.assertRaisesRegex(RuntimeError, "non_uat_database_host_configured"):
            reset_owner_beta_case(
                self.db,
                unsafe_settings,
                self.storage,
                RESET_CONFIRMATION,
            )

        self.assertFalse(self.storage.checked_ready)
        self.assertEqual(self.storage.ledger_entries, [])

    def test_reset_refuses_when_explicit_uat_reset_gate_is_disabled(self) -> None:
        disabled_settings = self.settings.model_copy(
            update={"owner_beta_fixture_reset_enabled": False}
        )

        with self.assertRaisesRegex(RuntimeError, "owner_beta_fixture_reset_disabled"):
            reset_owner_beta_case(
                self.db,
                disabled_settings,
                self.storage,
                RESET_CONFIRMATION,
            )

        self.assertFalse(self.storage.checked_ready)
        self.assertEqual(self.storage.ledger_entries, [])

    def test_reset_requires_exact_confirmation_before_accessing_storage(self) -> None:
        with self.assertRaisesRegex(ValueError, "RESET OWNER-BETA UAT CASE"):
            reset_owner_beta_case(
                self.db,
                self.settings,
                self.storage,
                "yes",
            )

        self.assertFalse(self.storage.checked_ready)

    def test_case_creation_registers_only_the_designated_owner_case(self) -> None:
        case = Case(status="draft", metadata_json={})
        self.db.add(case)
        self.db.flush()
        track_owner_beta_fixture_case(
            self.db,
            self.owner.id,
            case,
            self.settings,
        )
        self.db.commit()

        registry = self.db.get(OwnerBetaFixtureRegistry, self.owner.id)
        self.assertEqual(registry.case_id, case.id)

    def test_case_creation_rejects_a_different_case_when_registry_is_occupied(self) -> None:
        existing_case = self._register_case()
        new_case = Case(status="draft", metadata_json={})
        self.db.add(new_case)
        self.db.flush()

        with self.assertRaises(HTTPException) as raised:
            track_owner_beta_fixture_case(
                self.db,
                self.owner.id,
                new_case,
                self.settings,
            )

        self.assertEqual(raised.exception.status_code, 409)
        registry = self.db.get(OwnerBetaFixtureRegistry, self.owner.id)
        self.assertEqual(registry.case_id, existing_case.id)

    def test_case_creation_rejects_an_account_that_is_not_the_configured_owner(self) -> None:
        other_user = User(
            email="other@example.com",
            status="active",
            account_type="party",
            password_hash="hashed",
        )
        case = Case(status="draft", metadata_json={})
        self.db.add_all([other_user, case])
        self.db.flush()

        with self.assertRaises(HTTPException) as raised:
            track_owner_beta_fixture_case(
                self.db,
                other_user.id,
                case,
                self.settings,
            )

        self.assertEqual(raised.exception.status_code, 403)
        self.assertIsNone(self.db.get(OwnerBetaFixtureRegistry, other_user.id))
