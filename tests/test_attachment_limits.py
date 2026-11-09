import os
import threading
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import UUID, uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects import postgresql
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.attachment_limits import (
    MAX_ATTACHMENT_BYTES,
    attachment_count,
    attachment_limit,
    enforce_attachment_quota,
)
from app.auth_routes import require_current_user
from app.config import Settings
from app.database import Base, get_db
from app.main import app
from app.services import Artifact, store_artifacts
from app.models import Case, CaseMembership, Document, DocumentCreditLedgerEntry, User


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


PDF = b"%PDF-1.7\n"
FREE_SEED = 4


class AttachmentLimitTests(unittest.TestCase):
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
        self.user = User(email="owner@example.com", status="active")
        self.stranger = User(email="stranger@example.com", status="active")
        self.db.add_all([self.user, self.stranger])
        self.db.flush()
        self.case = Case(status="draft", metadata_json={})
        self.db.add(self.case)
        self.db.flush()
        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.user.id, role="owner"))
        self.db.commit()

        self.stored: dict[str, bytes] = {}
        storage = Mock()
        self.storage = storage
        storage.put.side_effect = lambda key, content, media: self.stored.__setitem__(key, content)
        storage.delete_all_versions.side_effect = lambda key: self.stored.pop(key, None)
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        for item in (
            patch("app.materials.get_settings", return_value=settings),
            patch("app.materials.storage", storage),
        ):
            item.start()
            self.addCleanup(item.stop)
        self.current_user = self.user
        app.dependency_overrides[require_current_user] = lambda: self.current_user

        def override_db():
            yield self.db

        app.dependency_overrides[get_db] = override_db
        self.client = TestClient(app)

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.db.close()
        for column, default in self._defaults:
            column.server_default = default

    def upload(self, content: bytes = PDF, *, batch=None, item=None, case_id="default"):
        batch = batch or uuid4()
        item = item or uuid4()
        data = {"case_id": str(self.case.id)} if case_id == "default" else {}
        return self.client.post(
            f"/api/v1/materials/imports/{batch}/files/{item}",
            files={"upload": (f"{item}.pdf", content, "application/pdf")},
            data=data,
        )

    def fill(self, count: int) -> None:
        for _ in range(count):
            self.assertEqual(self.upload().status_code, 201)

    def named_upload(self, name, content=PDF, *, batch=None, item=None, overwrite=None):
        data = {"case_id": str(self.case.id)}
        if overwrite is not None:
            data["overwrite_document_id"] = str(overwrite)
        return self.client.post(
            f"/api/v1/materials/imports/{batch or uuid4()}/files/{item or uuid4()}",
            data=data, files={"upload": (name, content, "application/pdf")},
        )

    def test_original_filename_preserved_and_duplicate_requires_explicit_confirmation(self) -> None:
        name = "Original \uc790\ub8cc 1.pdf"
        first = self.named_upload(name)
        self.assertEqual(first.status_code, 201, first.text)
        original_id = UUID(first.json()["document"]["id"])
        self.assertEqual(first.json()["document"]["original_filename"], name)
        response = self.named_upload(name, PDF + b"new")
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(response.json()["detail"]["code"], "filename_conflict")
        self.assertEqual(response.json()["detail"]["document_id"], str(original_id))
        self.assertEqual(attachment_count(self.db, self.case.id), 1)
        self.assertEqual(self.db.get(Document, original_id).original_filename, name)
        self.assertEqual(len(self.stored), 1)

    def test_confirmed_same_name_overwrite_at_full_quota_frees_old_file_and_keeps_name(self) -> None:
        first = self.named_upload("Evidence.pdf")
        original_id = UUID(first.json()["document"]["id"])
        self.case.metadata_json = {"existing_offer": {"exists": True, "document_ids": [str(original_id)]}}
        self.db.commit()
        original_key = self.db.get(Document, original_id).object_key
        self.fill(4)
        response = self.named_upload("Evidence.pdf", PDF + b"updated", overwrite=original_id)
        self.assertEqual(response.status_code, 201, response.text)
        new_id = UUID(response.json()["document"]["id"])
        self.assertNotEqual(new_id, original_id)
        self.assertIsNone(self.db.get(Document, original_id))
        self.assertEqual(self.db.get(Document, new_id).original_filename, "Evidence.pdf")
        self.assertNotIn(original_key, self.stored)
        self.assertEqual(attachment_count(self.db, self.case.id), 5)
        self.assertEqual(len(self.stored), 5)
        self.assertEqual(self.case.metadata_json["existing_offer"]["document_ids"], [str(new_id)])

    def test_overwrite_storage_failure_keeps_old_file_and_cleanup_failure_retries_without_uploading_again(self) -> None:
        first = self.named_upload("Evidence.pdf")
        original_id = UUID(first.json()["document"]["id"])
        self.fill(4)
        batch, item = uuid4(), uuid4()
        object_storage = self.storage
        original_put = object_storage.put.side_effect
        object_storage.put.side_effect = RuntimeError("Storage unavailable")
        response = self.named_upload("Evidence.pdf", PDF + b"updated", batch=batch, item=item, overwrite=original_id)
        self.assertEqual(response.status_code, 503, response.text)
        self.assertIsNotNone(self.db.get(Document, original_id))
        self.assertEqual(attachment_count(self.db, self.case.id), 5)
        object_storage.put.side_effect = original_put
        with patch("app.materials.delete_document_scope", side_effect=HTTPException(status_code=503, detail="Cleanup unavailable")):
            response = self.named_upload("Evidence.pdf", PDF + b"updated", batch=batch, item=item, overwrite=original_id)
        self.assertEqual(response.status_code, 503, response.text)
        self.assertEqual(attachment_count(self.db, self.case.id), 6)
        calls = object_storage.put.call_count
        response = self.named_upload("Evidence.pdf", PDF + b"updated", batch=batch, item=item, overwrite=original_id)
        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(object_storage.put.call_count, calls)
        self.assertEqual(attachment_count(self.db, self.case.id), 5)
        self.assertIsNone(self.db.get(Document, original_id))
        self.assertFalse(response.json()["document"]["overwrite_pending"])

    def test_different_retry_filename_or_stale_overwrite_target_cannot_change_saved_file(self) -> None:
        batch, item = uuid4(), uuid4()
        first = self.named_upload("Original.pdf", batch=batch, item=item)
        original_id = UUID(first.json()["document"]["id"])
        response = self.named_upload("Renamed.pdf", batch=batch, item=item)
        self.assertEqual(response.status_code, 409, response.text)
        response = self.named_upload("Different.pdf", overwrite=original_id)
        self.assertEqual(response.status_code, 409, response.text)
        response = self.named_upload("Original.pdf", overwrite=uuid4())
        self.assertEqual(response.status_code, 409, response.text)
        self.assertEqual(attachment_count(self.db, self.case.id), 1)
        self.assertEqual(self.db.get(Document, original_id).original_filename, "Original.pdf")

    def test_another_import_cannot_overwrite_while_cleanup_is_pending(self) -> None:
        first = self.named_upload("Evidence.pdf")
        original_id = UUID(first.json()["document"]["id"])
        with patch("app.materials.delete_document_scope", side_effect=HTTPException(status_code=503, detail="Cleanup unavailable")):
            response = self.named_upload("Evidence.pdf", PDF + b"updated", overwrite=original_id)
        self.assertEqual(response.status_code, 503, response.text)
        response = self.named_upload("Evidence.pdf", PDF + b"another", overwrite=original_id)
        self.assertEqual(response.status_code, 409, response.text)
        self.assertIn("previous overwrite", response.json()["detail"])
        self.assertEqual(attachment_count(self.db, self.case.id), 2)

    def test_default_limit_is_two_mebibytes(self) -> None:
        self.assertEqual(MAX_ATTACHMENT_BYTES, 2_097_152)
        self.assertEqual(Settings().max_upload_bytes, 2_097_152)

    def test_file_size_boundary(self) -> None:
        exact = PDF + b"x" * (MAX_ATTACHMENT_BYTES - len(PDF))
        self.assertEqual(self.upload(exact).status_code, 201)
        too_big = self.upload(exact + b"x")
        self.assertEqual(too_big.status_code, 413)
        self.assertIn("2097152", too_big.json()["detail"])
        self.assertEqual(attachment_count(self.db, self.case.id), 1)

    def test_free_quota_is_five_and_error_is_actionable(self) -> None:
        self.fill(5)
        response = self.upload()
        self.assertEqual(response.status_code, 409)
        self.assertIn("5 of 5", response.json()["detail"])
        self.assertIn("Remove an attachment", response.json()["detail"])
        self.assertEqual(attachment_count(self.db, self.case.id), 5)
        self.assertEqual(len(self.stored), 5)

    def test_paid_quota_is_one_hundred(self) -> None:
        self.db.add(
            DocumentCreditLedgerEntry(
                user_id=self.user.id,
                case_id=self.case.id,
                idempotency_key="stripe-checkout:cs_test",
                source_type="package_purchase",
                source_reference="cs_test",
                delta=5,
                balance_after=5,
            )
        )
        self.db.add_all(
            Document(
                case_id=self.case.id,
                object_key=f"{self.case.id}/seed-{n}.pdf",
                extension="pdf",
                media_type="application/pdf",
                sha256="0" * 64,
                size_bytes=1,
            )
            for n in range(99)
        )
        self.db.commit()
        self.assertEqual(attachment_limit(self.db, self.case.id), 100)
        self.assertEqual(self.upload().status_code, 201)
        self.assertEqual(self.upload().status_code, 409)

    def test_client_supplied_tier_is_ignored(self) -> None:
        self.fill(5)
        response = self.client.post(
            f"/api/v1/materials/imports/{uuid4()}/files/{uuid4()}?plan=paid&max_attachments=100",
            files={"upload": ("a.pdf", PDF, "application/pdf")},
            data={"case_id": str(self.case.id), "plan": "paid", "max_attachments": "100"},
            headers={"X-Plan": "paid"},
        )
        self.assertEqual(response.status_code, 409)

    def test_deletion_frees_slot_and_failed_deletion_does_not(self) -> None:
        self.fill(5)
        document = self.db.scalar(select(Document).where(Document.case_id == self.case.id))
        self.db.delete(document)
        self.db.commit()
        self.assertEqual(attachment_count(self.db, self.case.id), 4)
        self.assertEqual(self.upload().status_code, 201)
        self.assertEqual(self.upload().status_code, 409)

        self.db.rollback()
        self.assertEqual(attachment_count(self.db, self.case.id), 5)
        self.assertEqual(self.upload().status_code, 409)

    def test_batch_overflow_keeps_valid_files_without_duplicates(self) -> None:
        batch = uuid4()
        items = [uuid4() for _ in range(7)]
        statuses = [self.upload(PDF + bytes([n]), batch=batch, item=item).status_code for n, item in enumerate(items)]
        self.assertEqual(statuses, [201] * 5 + [409, 409])
        for n, item in enumerate(items[:5]):
            self.assertEqual(self.upload(PDF + bytes([n]), batch=batch, item=item).status_code, 201)
        self.assertEqual(attachment_count(self.db, self.case.id), 5)

    def test_retry_of_stored_item_does_not_consume_slot_at_limit(self) -> None:
        batch, item = uuid4(), uuid4()
        first = self.upload(batch=batch, item=item)
        self.fill(4)
        retry = self.upload(batch=batch, item=item)
        self.assertEqual(retry.status_code, 201)
        self.assertEqual(retry.json()["document"]["id"], first.json()["document"]["id"])
        self.assertEqual(attachment_count(self.db, self.case.id), 5)

    def test_rejected_item_can_be_retried_after_slot_frees(self) -> None:
        self.fill(5)
        batch, item = uuid4(), uuid4()
        self.assertEqual(self.upload(batch=batch, item=item).status_code, 409)
        self.db.delete(self.db.scalar(select(Document).where(Document.case_id == self.case.id)))
        self.db.commit()
        self.assertEqual(self.upload(batch=batch, item=item).status_code, 201)

    def test_new_case_import_is_allowed_and_config_reports_usage(self) -> None:
        self.current_user = self.stranger
        response = self.upload(case_id=None)
        self.assertEqual(response.status_code, 201)
        new_case = response.json()["case_id"]
        config = self.client.get(f"/api/v1/materials/config?case_id={new_case}").json()
        self.assertEqual((config["attachment_count"], config["max_attachments"]), (1, 5))
        self.current_user = self.user
        self.fill(2)
        config = self.client.get(f"/api/v1/materials/config?case_id={self.case.id}").json()
        self.assertEqual((config["attachment_count"], config["max_attachments"]), (2, 5))
        self.assertEqual(self.client.get("/api/v1/materials/config").json()["attachment_count"], 0)

    def test_non_member_cannot_upload_or_read_usage(self) -> None:
        self.current_user = self.stranger
        self.assertEqual(self.upload().status_code, 404)
        usage = self.client.get(f"/api/v1/materials/config?case_id={self.case.id}")
        self.assertEqual(usage.status_code, 404)
        self.assertEqual(attachment_count(self.db, self.case.id), 0)

    def test_quota_check_locks_case_row_before_counting(self) -> None:
        db = Mock()
        db.scalar.side_effect = [None, 0, None]
        enforce_attachment_quota(db, uuid4())
        statement = db.scalar.call_args_list[0].args[0]
        sql = str(statement.compile(dialect=postgresql.dialect()))
        self.assertIn("FOR UPDATE", sql)
        self.assertIn("cases", sql)

    def test_quota_is_rechecked_after_prior_transaction_ends(self) -> None:
        # Sequential only; real parallel behavior is PostgresConcurrentUploadTests.
        self.fill(4)
        enforce_attachment_quota(self.db, self.case.id)
        self.db.rollback()
        results = [self.upload().status_code, self.upload().status_code]
        self.assertEqual(sorted(results), [201, 409])

    def test_enforce_rejects_without_storing(self) -> None:
        self.fill(5)
        with self.assertRaises(HTTPException) as error:
            enforce_attachment_quota(self.db, self.case.id, 2)
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(self.db.scalar(select(func.count(Document.id))), 5)

    def test_case_document_routes_share_the_quota(self) -> None:
        storage = Mock()
        artifact = Artifact(PDF, "pdf", "application/pdf")
        for _ in range(4):
            store_artifacts(self.db, storage, self.case.id, [artifact])
        with self.assertRaises(HTTPException) as error:
            store_artifacts(self.db, storage, self.case.id, [artifact, artifact])
        self.assertEqual(error.exception.status_code, 409)
        self.assertEqual(storage.put.call_count, 4)
        store_artifacts(self.db, storage, self.case.id, [artifact])
        self.assertEqual(attachment_count(self.db, self.case.id), 5)


class AttachmentLimitUiTests(unittest.TestCase):
    def test_materials_ui_shows_usage_and_blocks_over_quota_without_truncating(self) -> None:
        html = (Path(__file__).parents[1] / "src/app/static/index.html").read_text(encoding="utf-8")
        for marker in (
            "config.attachment_count + pending.length > config.max_attachments",
            "Delete an unneeded file before adding another",
            "caseImportIdentities",
            "identity.documentId",
            "config.max_attachments",
        ):
            self.assertIn(marker, html)


POSTGRES_URL = os.environ.get("WA_TEST_POSTGRES_URL")


@unittest.skipUnless(
    POSTGRES_URL,
    "Set WA_TEST_POSTGRES_URL to a disposable PostgreSQL database to run concurrency tests.",
)
class PostgresConcurrentUploadTests(unittest.TestCase):
    """Two independent sessions race for the last slot; the case-row lock must admit one."""

    def setUp(self) -> None:
        self.schema = f"attachment_limits_{uuid4().hex[:12]}"
        admin = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
        with admin.connect() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{self.schema}"')
        admin.dispose()
        self.engine = create_engine(
            POSTGRES_URL, connect_args={"options": f"-csearch_path={self.schema}"}
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            user = User(email="owner@example.com", status="active")
            case = Case(status="draft", metadata_json={})
            db.add_all([user, case])
            db.flush()
            db.add(CaseMembership(case_id=case.id, user_id=user.id, role="owner"))
            db.add_all(
                Document(
                    case_id=case.id,
                    object_key=f"{case.id}/seed-{n}.pdf",
                    extension="pdf",
                    media_type="application/pdf",
                    sha256="0" * 64,
                    size_bytes=1,
                )
                for n in range(FREE_SEED)
            )
            db.commit()
            self.user_id, self.case_id = user.id, case.id

    def tearDown(self) -> None:
        app.dependency_overrides.clear()
        self.engine.dispose()
        admin = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{self.schema}" CASCADE')
        admin.dispose()

    def test_two_parallel_uploads_at_four_of_five_admit_exactly_one(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        user = SimpleNamespace(id=self.user_id)
        app.dependency_overrides[require_current_user] = lambda: user

        def override_db():
            with Session(self.engine) as db:
                yield db

        app.dependency_overrides[get_db] = override_db
        barrier = threading.Barrier(2, timeout=10)
        statuses: list[int] = []

        def attempt(n: int) -> None:
            client = TestClient(app)
            barrier.wait()
            response = client.post(
                f"/api/v1/materials/imports/{uuid4()}/files/{uuid4()}",
                files={"upload": ("a.pdf", PDF + bytes([n]), "application/pdf")},
                data={"case_id": str(self.case_id)},
            )
            statuses.append(response.status_code)

        with (
            patch("app.materials.get_settings", return_value=settings),
            patch("app.materials.storage", Mock()),
        ):
            threads = [threading.Thread(target=attempt, args=(n,)) for n in range(2)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join(timeout=30)

        self.assertEqual(sorted(statuses), [201, 409])
        with Session(self.engine) as db:
            self.assertEqual(attachment_count(db, self.case_id), 5)
