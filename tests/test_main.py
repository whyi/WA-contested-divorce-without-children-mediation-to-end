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
        self.assertIn("I have all documents demo", page)
        self.assertIn("Wizard demo", page)
        self.assertIn('id="signup-form"', page)
        self.assertIn('id="login-form"', page)
        self.assertIn('name="email" type="text" autocomplete="username"', page)
        self.assertIn('id="verify-form"', page)
        self.assertIn('href="#account">Sign up / Sign in', page)
        self.assertIn('id="demo-entry" href="/demo">Existing demo</a>', page)
        self.assertIn('href="/demo">Existing demo</a>', page)
        self.assertIn('class="demo-quick-section" id="demo-choices"', page)
        self.assertIn('class="demo-quick-link" href="/demo/documents"', page)
        self.assertIn("<strong>I have all documents demo</strong>", page)
        self.assertIn('class="demo-quick-link" href="/demo/wizard"', page)
        self.assertIn("<strong>Wizard demo</strong>", page)
        self.assertLess(page.index('id="demo-choices"'), page.index('class="hero"'))
        self.assertIn('id="documents-demo"', page)
        self.assertIn('id="wizard-demo"', page)
        self.assertIn('.authenticated-view .nav a:not(.demo-entry)', page)
        self.assertIn('const demoMode = window.location.pathname === "/demo";', page)
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
        self.assertIn('id="analysis-preview-start" type="button">Analyze</button>', page)
        self.assertIn('id="analysis-controls" aria-labelledby="analysis-title" hidden', page)
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

    def test_asset_analysis_preview_is_fictional_and_local_only(self) -> None:
        status, body = asyncio.run(request_app("/"))

        self.assertEqual(status, 200)
        page = body.decode()
        self.assertIn('id="analysis-preview-launch"', page)
        self.assertIn('id="asset-analysis-view"', page)
        self.assertIn("analysisPreviewLaunch.hidden = importedCount === 0;", page)
        self.assertIn(
            'analysisPreviewStartButton.addEventListener("click", openAssetAnalysis)',
            page,
        )
        self.assertEqual(page.count("loadAnalysisOptions("), 1)
        self.assertIn("<strong>Fictional example only.</strong>", page)
        self.assertIn("not based on your uploaded documents or case facts", page)
        self.assertIn('id="asset-table-rows"', page)
        self.assertIn('id="asset-table-total"', page)
        self.assertIn('id="asset-timeline-chart"', page)
        self.assertIn('id="asset-year-range" type="range"', page)
        self.assertIn('id="asset-year-previous"', page)
        self.assertIn('id="asset-year-next"', page)
        self.assertNotIn("asset-year-tab", page)
        self.assertIn('assetYearRange.addEventListener("input"', page)
        self.assertIn("renderAssetTimelineCursor(index)", page)
        self.assertIn("Best-case proposal", page)
        self.assertIn("Balanced proposal", page)
        self.assertIn("Fallback position", page)
        self.assertIn('id="scenario-status" role="status" aria-live="polite"', page)
        open_view = page.split("function openAssetAnalysis()", 1)[1].split(
            "function closeAssetAnalysis()", 1
        )[0]
        self.assertNotIn("fetch(", open_view)
        self.assertNotIn("sessionStorage", open_view)
        self.assertNotIn("/analysis-requests", open_view)

    def test_asset_comparison_edits_are_validated_accessible_and_local_only(
        self,
    ) -> None:
        status, body = asyncio.run(request_app("/"))

        self.assertEqual(status, 200)
        page = body.decode()
        self.assertIn('id="asset-edit-start" type="button">Edit values</button>', page)
        self.assertIn('id="asset-edit-save" type="button" hidden>Save changes</button>', page)
        self.assertIn('id="asset-edit-cancel" type="button" hidden>Cancel</button>', page)
        self.assertIn('id="asset-edit-status" role="status" aria-live="polite"', page)
        self.assertIn('id="asset-edit-error" role="alert" hidden', page)
        self.assertIn('role="group" aria-label="Edit fictional sample values"', page)
        edit_logic = page.split("function updateAssetEditControls()", 1)[1].split(
            "function createChartElement", 1
        )[0]
        self.assertIn("Number.isSafeInteger(value)", edit_logic)
        self.assertIn('input.dataset.assetEditCategory !== "debt" && value < 0', edit_logic)
        self.assertIn('input.setAttribute("aria-invalid", "true")', edit_logic)
        self.assertIn("sample[category] = assetEditDraft[category].map(Number)", edit_logic)
        self.assertIn("renderAssetTimeline();", edit_logic)
        self.assertIn("Unsaved edits canceled because you changed the selected year.", edit_logic)
        self.assertNotIn("localStorage", edit_logic)
        self.assertNotIn("sessionStorage", edit_logic)
        self.assertNotIn("indexedDB", edit_logic)
        self.assertIn('assetTableRows.addEventListener("input"', page)

    def test_asset_analysis_milestones_are_editable_accessible_and_local_only(
        self,
    ) -> None:
        status, body = asyncio.run(request_app("/"))

        self.assertEqual(status, 200)
        page = body.decode()
        self.assertIn('id="milestone-manager"', page)
        self.assertIn("<summary>Manage milestone dates</summary>", page)
        self.assertIn('id="standard-milestone-list"', page)
        manager = page.split('id="milestone-manager"', 1)[1].split("</details>", 1)[0]
        self.assertIn('id="standard-milestone-list"', manager)
        self.assertIn('id="custom-milestone-form"', manager)
        self.assertNotIn('id="standard-milestone-editor"', page)
        self.assertIn('id="custom-milestone-list"', page)
        self.assertIn('id="asset-milestone-selector"', page)
        self.assertIn('dateInput.setAttribute("aria-label", `${milestone.label} date`)', page)
        self.assertIn('id="asset-chart-milestones" aria-label="Relationship milestone markers"', page)
        self.assertIn('id="asset-milestone-status" role="status" aria-live="polite"', page)
        self.assertIn('id: "separation", label: "Separation", date: ""', page)
        self.assertIn("option.disabled = !milestone.custom;", page)
        self.assertIn('textContent = `${milestone.label} — N/A`', page)
        self.assertIn("milestone.overrideDate = date;", page)
        self.assertIn('window.addEventListener("casework:milestones-extracted"', page)
        self.assertIn("applyExtractedMilestoneDates(event.detail)", page)
        self.assertIn('milestone.source = "extracted";', page)
        self.assertIn("document-analyzed milestone date(s) added for review", page)
        self.assertIn('confirm.dataset.action = "confirm-delete"', page)
        self.assertIn("isValidMilestoneDate(date)", page)
        self.assertIn("This date is outside the displayed asset timeline", page)
        self.assertIn("selectAssetMilestone(marker.dataset.milestoneId)", page)
        milestone_logic = page.split(
            "function milestoneActiveDate(milestone)", 1
        )[1].split("function renderAssetSnapshot(index)", 1)[0]
        self.assertNotIn("fetch(", milestone_logic)
        self.assertNotIn("localStorage", milestone_logic)
        self.assertNotIn("sessionStorage", milestone_logic)

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
            asyncio.run(request_app("/demo")),
            asyncio.run(request_app("/demo/documents")),
            asyncio.run(request_app("/demo/wizard")),
        )

        self.assertEqual([status for status, _ in responses], [200, 200, 200, 200, 200])
        for _, body in responses[:2]:
            page = body.decode()
            self.assertIn('id="account-dashboard"', page)
            self.assertIn('"/api/v1/dashboard/status"', page)
            self.assertIn("This preview does not accept or save case details or documents.", page)
        demo_page = responses[2][1].decode()
        self.assertIn('const demoMode = window.location.pathname === "/demo";', demo_page)
        self.assertIn("Explore fictional sample figures without signing in or opening a case.", demo_page)
        self.assertIn('showPreparation("demo");', demo_page)
        document_demo_page = responses[3][1].decode()
        self.assertIn('const demoDocumentsMode = window.location.pathname === "/demo/documents";', document_demo_page)
        self.assertIn('id="demo-file-input" type="file"', document_demo_page)
        self.assertIn('id="demo-files-next" type="button" disabled', document_demo_page)
        self.assertIn("Only PDF and DOCX files are supported.", document_demo_page)
        self.assertIn('window.location.assign("/demo")', document_demo_page)
        wizard_demo_page = responses[4][1].decode()
        self.assertIn('id="wizard-filed-question"', wizard_demo_page)
        self.assertIn('id="wizard-role-question" disabled', wizard_demo_page)
        self.assertIn('<dialog class="demo-wizard-dialog"', wizard_demo_page)
        self.assertIn("wizardFiledDialog.addEventListener(\"cancel\", (event) => event.preventDefault())", wizard_demo_page)
        self.assertIn('id="wizard-gated-content" hidden', wizard_demo_page)
        self.assertIn('data-wizard-date="cohabitation"', wizard_demo_page)
        self.assertIn('data-wizard-date="marriage"', wizard_demo_page)
        self.assertIn('data-wizard-date="separation"', wizard_demo_page)
        self.assertIn('data-wizard-date="petition"', wizard_demo_page)
        self.assertIn('id="wizard-finance-list"', wizard_demo_page)
        self.assertIn('id="wizard-issue-list"', wizard_demo_page)
        self.assertIn('id="wizard-agreement-list"', wizard_demo_page)
        self.assertIn('id="wizard-review-list"', wizard_demo_page)
        self.assertIn('id="wizard-clear-dialog"', wizard_demo_page)
        self.assertIn('id="wizard-finish" type="button" disabled>Save and view Existing demo', wizard_demo_page)
        self.assertIn('indexedDB.open(wizardDatabaseName, wizardDatabaseVersion)', wizard_demo_page)
        self.assertIn('wizardDatabaseName = "casework-wizard-intake"', wizard_demo_page)
        self.assertIn("Restored the draft and attached files saved in this browser.", wizard_demo_page)
        self.assertNotIn("localStorage.setItem", wizard_demo_page)
        wizard_change_handler = wizard_demo_page.split(
            "function handleWizardChange(event)", 1
        )[1].split("function addWizardEntry", 1)[0]
        self.assertNotIn("fetch(", wizard_change_handler)
        demo_bootstrap = demo_page.rsplit('if (demoMode) {', 1)[1].split(
            "} else {", 1
        )[0]
        self.assertNotIn("fetch(", demo_bootstrap)
        self.assertNotIn("loadDashboardStatus(", demo_bootstrap)


if __name__ == "__main__":
    unittest.main()
