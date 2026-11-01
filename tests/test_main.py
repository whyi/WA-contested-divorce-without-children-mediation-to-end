import asyncio
import unittest
from types import SimpleNamespace
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, Mock, patch

from botocore.exceptions import BotoCoreError
from fastapi import HTTPException
from sqlalchemy.exc import SQLAlchemyError

from app.config import Settings
from app.database import get_db
from app.main import app, delete_document, preview_document
from app.models import AuthSession, CaseMembership, Document, User


async def request_app(
    path: str,
    method: str = "GET",
    body: bytes = b"",
    headers: list[tuple[bytes, bytes]] | None = None,
) -> tuple[int, bytes]:
    sent_request = False
    messages: list[dict] = []

    async def receive() -> dict:
        nonlocal sent_request
        if not sent_request:
            sent_request = True
            return {"type": "http.request", "body": body, "more_body": False}
        await asyncio.Future()
        return {"type": "http.disconnect"}

    async def send(message: dict) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0", "spec_version": "2.3"},
        "http_version": "1.1",
        "method": method,
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "root_path": "",
        "headers": headers or [],
        "server": ("testserver", 80),
        "client": ("testclient", 12345),
    }
    await app(scope, receive, send)
    response_start = next(
        message for message in messages if message["type"] == "http.response.start"
    )
    response_body = b"".join(
        message.get("body", b"")
        for message in messages
        if message["type"] == "http.response.body"
    )
    return response_start["status"], response_body


class MainWorkflowTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_root_displays_mode_choices_and_authentication_gate(self) -> None:
        status, body = asyncio.run(request_app("/"))

        self.assertEqual(status, 200)
        page = body.decode()
        self.assertIn("I have the documents. Help me sort them.", page)
        self.assertIn("Walk me through it, step by step.", page)
        self.assertIn('id="signup-form"', page)
        self.assertIn('id="login-form"', page)
        self.assertIn('name="email" type="text" autocomplete="username"', page)
        self.assertIn("username <strong>demo</strong> · password <strong>demo</strong>", page)
        self.assertIn('id="verify-form"', page)
        self.assertIn('href="#account">Sign up / Sign in', page)
        self.assertIn('id="demo-button"', page)
        self.assertIn('demoButton.addEventListener("click"', page)
        self.assertIn('"/api/auth/signup"', page)
        self.assertIn('"/api/auth/login"', page)
        self.assertIn('"/api/auth/verify-email"', page)
        self.assertIn('id="google-signin"', page)
        self.assertIn('"/api/auth/providers"', page)
        self.assertIn('"/api/auth/oidc/google/start"', page)
        self.assertIn("Case workspaces remain unavailable in this preview.", page)
        self.assertIn("Illustrative interface — not an active case", page)
        self.assertIn('id="account-dashboard"', page)
        self.assertIn('id="dashboard-loading" role="status"', page)
        self.assertIn("I already have case materials, so I'll upload them", page)
        self.assertIn("Guide me through the wizard step by step", page)
        self.assertIn('id="materials-workflow"', page)
        self.assertIn('id="materials-file-input"', page)
        self.assertIn('id="google-drive-picker"', page)
        self.assertIn('id="dropbox-picker"', page)
        self.assertIn('id="materials-import"', page)
        self.assertIn('"/api/v1/materials/config"', page)
        self.assertIn('id="analysis-preview-notice"', page)
        self.assertIn("AWS Bedrock in us-east-2", page)
        self.assertIn("Disclosure only—not consent", page)
        self.assertIn("Importing a file stores it in your case workspace", page)
        self.assertIn("Only after you select documents and explicitly consent", page)
        self.assertIn('id="analysis-controls"', page)
        self.assertIn('id="analysis-consent"', page)
        self.assertIn('id="analysis-provider"', page)
        self.assertIn('id="analysis-status"', page)
        self.assertIn('id="proposal-review"', page)
        self.assertIn('id="review-status" role="status" aria-live="polite"', page)
        self.assertIn('id="review-proposals"', page)
        self.assertIn('id="profile-facts-list"', page)
        self.assertIn('id="adopt-selected-proposals"', page)
        self.assertIn('adoptionConfirm.addEventListener("change", renderAdoptionSummary)', page)
        self.assertIn('adoptSelectedButton.addEventListener("click", adoptSelectedProposals)', page)
        self.assertIn("Previously adopted case-profile facts are shown below.", page)
        self.assertIn('id="dashboard-retry"', page)
        self.assertIn('"/api/v1/dashboard/status"', page)

    def test_case_data_endpoints_fail_closed_until_authentication_is_configured(
        self,
    ) -> None:
        case_id = uuid4()
        requests = (
            asyncio.run(request_app("/cases", "POST", b'{"metadata":{}}')),
            asyncio.run(request_app(f"/cases/{case_id}")),
            asyncio.run(
                request_app(
                    f"/documents/{uuid4()}/download",
                )
            ),
            asyncio.run(request_app(f"/documents/{uuid4()}", "DELETE")),
            asyncio.run(
                request_app(
                    f"/cases/{case_id}/documents/{uuid4()}/extraction-status",
                )
            ),
            asyncio.run(request_app(f"/cases/{case_id}/analysis/options")),
            asyncio.run(
                request_app(
                    f"/cases/{case_id}/analysis-requests",
                    "POST",
                    b'{"idempotency_key":"'
                    + str(uuid4()).encode()
                    + b'","document_ids":["'
                    + str(uuid4()).encode()
                    + b'"],"notice_version":"notice-1","consent":true}',
                )
            ),
            asyncio.run(request_app(f"/documents/{uuid4()}/preview")),
            asyncio.run(
                request_app(
                    f"/cases/{case_id}/documents/{uuid4()}/source-text",
                )
            ),
            asyncio.run(
                request_app(
                    f"/cases/{case_id}/profile-facts",
                )
            ),
            asyncio.run(
                request_app(
                    f"/cases/{case_id}/analysis-requests/{uuid4()}/review",
                )
            ),
            asyncio.run(
                request_app(
                    f"/cases/{case_id}/profile-facts/adoptions",
                    "POST",
                    b"{}",
                )
            ),
        )

        self.assertEqual(
            [status for status, _ in requests],
            [503, 503, 503, 503, 503, 503, 503, 503, 503, 503, 503, 503],
        )
        for _, body in requests:
            self.assertIn(b"Authentication is not configured", body)

    def test_document_deletion_removes_the_object_and_metadata(self) -> None:
        document_id = uuid4()
        document = SimpleNamespace(object_key="case/document.pdf")
        db = Mock()
        db.get.return_value = document

        with patch("app.main.storage") as object_storage:
            response = delete_document(document_id, db)

        self.assertEqual(response.status_code, 204)
        object_storage.delete.assert_called_once_with("case/document.pdf")
        db.delete.assert_called_once_with(document)
        db.commit.assert_called_once()

    def test_pdf_preview_is_inline_and_not_cacheable(self) -> None:
        document_id = uuid4()
        document = SimpleNamespace(
            id=document_id,
            object_key="case/document.pdf",
            extension="pdf",
            media_type="application/pdf",
        )
        db = Mock()
        db.get.return_value = document

        with patch("app.main.storage") as object_storage:
            object_storage.get.return_value = b"%PDF-1.7"
            response = preview_document(document_id, db)

        self.assertEqual(response.body, b"%PDF-1.7")
        self.assertEqual(response.media_type, "application/pdf")
        self.assertIn("inline", response.headers["content-disposition"])
        self.assertEqual(response.headers["cache-control"], "no-store")
        object_storage.get.assert_called_once_with("case/document.pdf")

    def test_document_deletion_reports_incomplete_metadata_cleanup(self) -> None:
        document = SimpleNamespace(object_key="case/document.pdf")
        db = Mock()
        db.get.return_value = document
        db.commit.side_effect = SQLAlchemyError("database unavailable")

        with (
            patch("app.main.storage") as object_storage,
            self.assertRaises(HTTPException) as raised,
        ):
            delete_document(uuid4(), db)

        self.assertEqual(raised.exception.status_code, 503)
        object_storage.delete.assert_called_once_with("case/document.pdf")
        db.rollback.assert_called_once()

    def test_document_deletion_keeps_metadata_when_object_removal_fails(self) -> None:
        document = SimpleNamespace(object_key="case/document.pdf")
        db = Mock()
        db.get.return_value = document

        with (
            patch("app.main.storage") as object_storage,
            self.assertRaises(HTTPException) as raised,
        ):
            object_storage.delete.side_effect = BotoCoreError()
            delete_document(uuid4(), db)

        self.assertEqual(raised.exception.status_code, 503)
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    def test_document_deletion_requires_case_membership_and_non_viewer_role(self) -> None:
        user_id = uuid4()
        session_id = uuid4()
        document_id = uuid4()
        case_id = uuid4()
        now = datetime.now(UTC)
        auth_session = SimpleNamespace(
            user_id=user_id,
            revoked_at=None,
            idle_expires_at=now + timedelta(days=1),
            absolute_expires_at=now + timedelta(days=2),
        )
        user = SimpleNamespace(id=user_id, status="active")
        document = SimpleNamespace(
            id=document_id,
            case_id=case_id,
            object_key="case/document.pdf",
            media_type="application/pdf",
            extension="pdf",
            sha256="f" * 64,
        )
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="secure-test-signing-secret-that-is-long-enough",
            case_data_enabled=True,
            s3_kms_key_id="alias/test-case-materials",
            demo_mode_enabled=False,
        )

        for method, role, expected_status in (
            ("DELETE", "owner", 204),
            ("DELETE", "viewer", 403),
            ("GET", "viewer", 200),
            ("STATUS", "viewer", 200),
            ("DELETE", None, 404),
            ("GET", None, 404),
            ("STATUS", None, 404),
        ):
            with self.subTest(method=method, role=role):
                db = Mock()
                db.get.side_effect = lambda model, key: {
                    AuthSession: auth_session,
                    User: user,
                    Document: document,
                }.get(model)
                membership = (
                    SimpleNamespace(role=role)
                    if role is not None
                    else None
                )
                if method == "STATUS":
                    db.scalar.side_effect = [membership, None, None]
                else:
                    db.scalar.return_value = membership
                app.dependency_overrides[get_db] = lambda: db
                session_context = MagicMock()
                session_context.__enter__.return_value = db
                session_factory = Mock(return_value=session_context)
                with (
                    patch("app.main.settings", settings),
                    patch("app.main.SessionLocal", session_factory),
                    patch(
                        "app.main.verify_token",
                        return_value={"sub": str(user_id), "sid": str(session_id)},
                    ),
                    patch("app.main.storage") as object_storage,
                ):
                    object_storage.get.return_value = b"private"
                    path = {
                        "GET": f"/documents/{document_id}/download",
                        "STATUS": f"/cases/{case_id}/documents/{document_id}/extraction-status",
                    }.get(method, f"/documents/{document_id}")
                    request_method = "GET" if method == "STATUS" else method
                    status, _ = asyncio.run(
                        request_app(
                            path,
                            request_method,
                            headers=[
                                (b"cookie", b"auth_access=test; auth_csrf=csrf"),
                                (b"x-csrf-token", b"csrf"),
                            ],
                        )
                    )

                self.assertEqual(status, expected_status)
                if method == "DELETE" and role == "owner":
                    object_storage.delete.assert_called_once_with("case/document.pdf")
                elif method == "GET" and role == "viewer":
                    object_storage.get.assert_called_once_with("case/document.pdf")
                else:
                    object_storage.delete.assert_not_called()
                    object_storage.get.assert_not_called()
                app.dependency_overrides.clear()

    def test_onboarding_paths_serve_the_authenticated_preview_page(self) -> None:
        responses = (
            asyncio.run(request_app("/onboarding/upload")),
            asyncio.run(request_app("/onboarding/wizard")),
        )

        self.assertEqual([status for status, _ in responses], [200, 200])
        for _, body in responses:
            page = body.decode()
            self.assertIn('id="account-dashboard"', page)
            self.assertIn('"/api/v1/dashboard/status"', page)
            self.assertIn("This preview does not accept or save case details or documents.", page)

if __name__ == "__main__":
    unittest.main()
