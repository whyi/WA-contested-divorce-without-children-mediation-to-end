import hashlib
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi.testclient import TestClient
from botocore.exceptions import BotoCoreError
from sqlalchemy.exc import SQLAlchemyError

from app.auth_routes import require_current_user
from app.config import Settings
from app.database import get_db
from app.main import app
from app.materials import _delete_uploaded_object
from app.models import Case, CaseMembership, DocumentExtractionJob, MaterialImportBatch, User


class MaterialsImportTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def _client(self, user_id=None, db=None):
        user = SimpleNamespace(id=user_id or uuid4())
        app.dependency_overrides[require_current_user] = lambda: user
        if db is not None:
            def override_db():
                yield db

            app.dependency_overrides[get_db] = override_db
        return TestClient(app), user

    def test_config_reports_runtime_upload_limit_and_unconfigured_providers(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            max_upload_bytes=12345,
            demo_mode_enabled=False,
        )
        client, _ = self._client()
        with patch("app.materials.get_settings", return_value=settings):
            response = client.get("/api/v1/materials/config")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "max_upload_bytes": 12345,
                "supported_extensions": ["pdf", "docx"],
                "import_enabled": False,
                "providers": {"google_drive": False, "dropbox": False},
            },
        )

    def test_import_fails_closed_when_case_data_is_disabled(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=False,
            demo_mode_enabled=False,
        )
        client, _ = self._client(db=Mock())
        with patch("app.materials.get_settings", return_value=settings):
            response = client.post(
                f"/api/v1/materials/imports/{uuid4()}/files/{uuid4()}",
                files={"upload": ("evidence.pdf", b"%PDF-1.7\ncontent", "application/pdf")},
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("secure material storage is enabled", response.json()["detail"])

    def test_import_validates_file_before_creating_a_case(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        db = Mock()
        client, _ = self._client(db=db)
        with patch("app.materials.get_settings", return_value=settings):
            response = client.post(
                f"/api/v1/materials/imports/{uuid4()}/files/{uuid4()}",
                files={"upload": ("notes.txt", b"private text", "text/plain")},
            )

        self.assertEqual(response.status_code, 415)
        db.add_all.assert_not_called()
        db.commit.assert_not_called()

    def test_successful_import_creates_one_owned_draft_and_stores_the_file(self) -> None:
        user_id = uuid4()
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        db = Mock()
        user = SimpleNamespace(id=user_id)
        db.get.side_effect = lambda model, key, **kwargs: user if model is User else None
        db.scalar.return_value = 0
        client, _ = self._client(user_id=user_id, db=db)
        batch_id = uuid4()
        item_id = uuid4()
        content = b"%PDF-1.7\nvalid test document"
        with (
            patch("app.materials.get_settings", return_value=settings),
            patch("app.materials.storage") as object_storage,
        ):
            response = client.post(
                f"/api/v1/materials/imports/{batch_id}/files/{item_id}",
                files={"upload": ("evidence.pdf", content, "application/pdf")},
            )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["item_id"], str(item_id))
        self.assertEqual(response.json()["document"]["size_bytes"], len(content))
        object_storage.put.assert_called_once()
        db.commit.assert_called_once()
        added = db.add_all.call_args.args[0]
        created_case = db.add.call_args_list[0].args[0]
        self.assertIsInstance(created_case, Case)
        self.assertEqual(created_case.status, "draft")
        memberships = [
            call.args[0] for call in db.add.call_args_list
            if isinstance(call.args[0], CaseMembership)
        ]
        self.assertEqual(len(memberships), 1)
        self.assertEqual(memberships[0].user_id, user_id)
        self.assertEqual(memberships[0].role, "owner")
        self.assertIsInstance(added[0], MaterialImportBatch)
        self.assertEqual(added[0].user_id, user_id)
        self.assertEqual(added[0].id, batch_id)
        self.assertFalse(any(isinstance(record, DocumentExtractionJob) for record in added))

    def test_import_uses_the_dashboard_case_instead_of_creating_another(self) -> None:
        user_id = uuid4()
        case_id = uuid4()
        user = SimpleNamespace(id=user_id)
        case = Case(id=case_id, status="draft")
        db = Mock()
        db.get.side_effect = lambda model, key, **kwargs: (
            user if model is User else case if model is Case and key == case_id else None
        )
        db.scalar.return_value = SimpleNamespace(role="owner")
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        client, _ = self._client(user_id=user_id, db=db)
        with (
            patch("app.materials.get_settings", return_value=settings),
            patch("app.materials.storage") as object_storage,
        ):
            response = client.post(
                f"/api/v1/materials/imports/{uuid4()}/files/{uuid4()}",
                data={"case_id": str(case_id)},
                files={"upload": ("evidence.pdf", b"%PDF-1.7\ncontent", "application/pdf")},
            )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["case_id"], str(case_id))
        self.assertFalse(any(isinstance(call.args[0], Case) for call in db.add.call_args_list))
        self.assertEqual(db.scalar.call_count, 1)
        object_storage.put.assert_called_once()

    def test_import_cannot_create_a_second_party_owned_case(self) -> None:
        user_id = uuid4()
        user = SimpleNamespace(id=user_id)
        db = Mock()
        db.get.side_effect = lambda model, key, **kwargs: user if model is User else None
        db.scalar.return_value = 1
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        client, _ = self._client(user_id=user_id, db=db)
        with (
            patch("app.materials.get_settings", return_value=settings),
            patch("app.materials.storage") as object_storage,
        ):
            response = client.post(
                f"/api/v1/materials/imports/{uuid4()}/files/{uuid4()}",
                files={"upload": ("evidence.pdf", b"%PDF-1.7\ncontent", "application/pdf")},
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("can own one divorce case", response.json()["detail"])
        object_storage.put.assert_not_called()
        db.commit.assert_not_called()

    def test_retry_returns_existing_document_without_uploading_again(self) -> None:
        user_id = uuid4()
        case_id = uuid4()
        batch_id = uuid4()
        item_id = uuid4()
        document_id = uuid4()
        batch = SimpleNamespace(user_id=user_id, case_id=case_id)
        item = SimpleNamespace(id=uuid4(), document_id=document_id)
        document = SimpleNamespace(
            id=document_id,
            extension="pdf",
            media_type="application/pdf",
            size_bytes=20,
            sha256=hashlib.sha256(b"%PDF-1.7\ncontent").hexdigest(),
        )
        db = Mock()
        db.get.side_effect = lambda model, key: batch if model is MaterialImportBatch else document
        db.scalar.return_value = item
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        client, _ = self._client(user_id=user_id, db=db)
        with (
            patch("app.materials.get_settings", return_value=settings),
            patch("app.materials.storage") as object_storage,
        ):
            response = client.post(
                f"/api/v1/materials/imports/{batch_id}/files/{item_id}",
                files={"upload": ("evidence.pdf", b"%PDF-1.7\ncontent", "application/pdf")},
            )

        self.assertEqual(response.status_code, 201, response.text)
        self.assertEqual(response.json()["document"]["id"], str(document_id))
        object_storage.put.assert_not_called()
        db.commit.assert_not_called()

    def test_retry_rejects_reusing_an_item_key_for_different_file_contents(self) -> None:
        user_id, case_id, batch_id, item_id, document_id = (uuid4() for _ in range(5))
        user = SimpleNamespace(id=user_id)
        batch = SimpleNamespace(user_id=user_id, case_id=case_id)
        item = SimpleNamespace(id=uuid4(), document_id=document_id)
        original = b"%PDF-1.7\noriginal source"
        document = SimpleNamespace(
            id=document_id,
            extension="pdf",
            media_type="application/pdf",
            size_bytes=len(original),
            sha256=hashlib.sha256(original).hexdigest(),
        )
        db = Mock()
        db.get.side_effect = lambda model, key, **kwargs: (
            user if model is User else batch if model is MaterialImportBatch else document
        )
        db.scalar.side_effect = [item, SimpleNamespace(role="owner")]
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        client, _ = self._client(user_id=user_id, db=db)
        with (
            patch("app.materials.get_settings", return_value=settings),
            patch("app.materials.storage") as object_storage,
        ):
            response = client.post(
                f"/api/v1/materials/imports/{batch_id}/files/{item_id}",
                files={"upload": ("evidence.pdf", b"%PDF-1.7\ndifferent source", "application/pdf")},
            )

        self.assertEqual(response.status_code, 409)
        self.assertIn("different file contents", response.json()["detail"])
        object_storage.put.assert_not_called()
        db.commit.assert_not_called()

    def test_database_failure_cleans_up_the_uploaded_object(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="materials-test-signing-secret-long-enough",
            case_data_enabled=True,
            case_materials_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )
        db = Mock()
        user = SimpleNamespace(
            id=uuid4(),
            subscription_plan="free",
            subscription_status="free",
        )
        db.get.side_effect = lambda model, key, **kwargs: user if model is User else None
        db.scalar.return_value = 0
        db.commit.side_effect = SQLAlchemyError("database unavailable")
        client, _ = self._client(db=db)
        with (
            patch("app.materials.get_settings", return_value=settings),
            patch("app.materials.storage") as object_storage,
        ):
            response = client.post(
                f"/api/v1/materials/imports/{uuid4()}/files/{uuid4()}",
                files={"upload": ("evidence.pdf", b"%PDF-1.7\ncontent", "application/pdf")},
            )

        self.assertEqual(response.status_code, 503)
        db.rollback.assert_called_once()
        object_storage.put.assert_called_once()
        object_storage.delete.assert_called_once()

    def test_cleanup_failure_logs_no_object_key(self) -> None:
        object_key = "private-case/private-document.pdf"
        with (
            patch("app.materials.storage") as object_storage,
            self.assertLogs("app.materials", level="ERROR") as captured,
        ):
            object_storage.delete.side_effect = BotoCoreError()
            _delete_uploaded_object(object_key)

        self.assertNotIn(object_key, "\n".join(captured.output))


if __name__ == "__main__":
    unittest.main()
