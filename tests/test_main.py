import asyncio
import re
import unittest
from types import SimpleNamespace
from datetime import UTC, datetime, timedelta
from uuid import uuid4
from unittest.mock import MagicMock, Mock, patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.config import Settings
from app.database import get_db
from app.main import (
    CaseCreate,
    OAuthCallbackQueryFilter,
    app,
    create_case,
    delete_document,
    lifespan,
    preview_document,
    readiness,
    read_property_tracing,
    update_property_tracing,
)
from app.deletion import PermanentDeletionConfirmation
from app.models import AuthSession, Case, CaseMembership, Document, User
from app.property_tracing import PropertyTracingUpdate


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
    def test_production_case_data_routes_fail_closed_without_counsel_evidence(self) -> None:
        settings = Settings(production_readiness_required=True)
        with patch("app.main.settings", settings):
            response = TestClient(app).get("/cases")

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            response.json(),
            {"detail": "Production readiness requirements are unmet."},
        )

    def test_case_data_startup_reconciles_external_deletion_ledger(self) -> None:
        async def start_application():
            async with lifespan(app):
                return

        with (
            patch(
                "app.main.settings",
                SimpleNamespace(demo_mode_enabled=False, case_data_enabled=True),
            ),
            patch("app.deletion_ledger.reconcile_from_environment") as reconcile,
        ):
            asyncio.run(start_application())

        reconcile.assert_called_once_with()

    def test_readiness_fails_closed_when_deletion_protection_is_unavailable(self) -> None:
        with patch(
            "app.main.storage.check_ready",
            side_effect=RuntimeError("ledger marker missing"),
        ), patch("app.main.SessionLocal", MagicMock()):
            with self.assertRaises(HTTPException) as raised:
                readiness()

        self.assertEqual(raised.exception.status_code, 503)
        self.assertIn("Permanent-deletion protection", raised.exception.detail)

    def test_party_case_ownership_is_enforced_with_a_user_lock(self) -> None:
        user_id = uuid4()
        user = SimpleNamespace()
        db = Mock()
        db.get.return_value = user
        db.scalar.return_value = 1
        request = SimpleNamespace(state=SimpleNamespace(user_id=user_id))

        with self.assertRaises(HTTPException) as raised:
            create_case(CaseCreate(), request, db)

        self.assertEqual(raised.exception.status_code, 409)
        db.get.assert_called_once_with(User, user_id, with_for_update=True)
        db.add.assert_not_called()

    def test_create_case_saves_dashboard_title_and_starting_workflow(self) -> None:
        user_id = uuid4()
        db = Mock()
        db.get.return_value = SimpleNamespace(
        )
        db.scalar.return_value = 0
        request = SimpleNamespace(state=SimpleNamespace(user_id=user_id))

        case = create_case(
            CaseCreate(case_title="  XYZ vs ABC  ", workflow_mode="wizard"),
            request,
            db,
        )

        self.assertEqual(case.metadata_json, {
            "case_title": "XYZ vs ABC",
            "workflow_mode": "wizard",
        })
        self.assertEqual(case.status, "draft")
        db.commit.assert_called_once()

    def test_oauth_callback_access_logs_redact_query_credentials(self) -> None:
        import logging

        record = logging.LogRecord(
            "uvicorn.access",
            logging.INFO,
            __file__,
            1,
            '%s - "%s %s HTTP/%s" %d',
            (
                "127.0.0.1",
                "GET",
                "/api/export-integrations/google_drive/callback?code=secret&state=state",
                "1.1",
                200,
            ),
            None,
        )

        OAuthCallbackQueryFilter().filter(record)

        self.assertNotIn("secret", record.getMessage())
        self.assertNotIn("state", record.getMessage())

    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_theme_selection_persistence_and_shared_page_coverage(self) -> None:
        pages = []
        for path in ("/", "/demo", "/demo/wizard"):
            status, body = asyncio.run(request_app(path))
            self.assertEqual(status, 200)
            pages.append(body.decode())

        for page in pages:
            self.assertIn('<label class="theme-control" for="theme-select">', page)
            self.assertIn('<select id="theme-select" name="theme">', page)
            self.assertIn('<option value="system">System</option>', page)
            self.assertIn('<option value="light">Light</option>', page)
            self.assertIn('<option value="dark">Dark</option>', page)
            self.assertIn('id="theme-status" role="status" aria-live="polite"', page)
            self.assertIn(':root[data-theme="dark"]', page)
            self.assertIn("color-scheme: dark", page)
            self.assertIn("--chart-you:", page)
            self.assertIn("--chart-other:", page)
            self.assertIn("--chart-combined:", page)
            self.assertIn("prefers-reduced-motion: reduce", page)

        page = pages[0]
        self.assertIn(".settlement-demo-scenario-choice", page)
        self.assertIn("data-selected", page)
        self.assertIn("accent-color: var(--green)", page)
        bootstrap = page.split("<script>", 1)[1].split("</script>", 1)[0]
        self.assertLess(page.index("</script>"), page.index("<style>"))
        self.assertIn('getItem("casework-theme")', bootstrap)
        self.assertIn('dataset.themePreference = preference', bootstrap)
        self.assertIn('dataset.theme = theme', bootstrap)
        self.assertIn('matchMedia("(prefers-color-scheme: dark)")', bootstrap)
        self.assertIn("catch", bootstrap)

        theme_handler = page.split('const themeSelect =', 1)[1].split(
            'const signupTab =', 1
        )[0]
        self.assertIn('setItem(themePreferenceKey, preference)', theme_handler)
        self.assertIn('addEventListener("change", handleSystemThemeChange)', theme_handler)
        self.assertIn('addListener(handleSystemThemeChange)', theme_handler)
        self.assertIn('dispatchEvent(new Event("casework:themechange"))', theme_handler)
        self.assertIn('resolvedTheme === "dark" ? "#121a16" : "#f7f8f6"', theme_handler)
        self.assertNotIn("fetch(", theme_handler)

        css = page.split("<style>", 1)[1].split("</style>", 1)[0]
        component_css = css.split(".preview-bar {", 1)[1]
        declaration = re.compile(
            r"(?P<property>background(?:-color)?|border(?:-(?:top|right|bottom|left|color))?|outline(?:-color)?|accent-color|color|fill|stroke)\s*:\s*(?P<value>[^;{}]+)",
            re.IGNORECASE,
        )
        for rule in declaration.finditer(component_css):
            self.assertNotRegex(
                rule.group("value"),
                r"#[0-9a-fA-F]{3}(?:[0-9a-fA-F]{3})?\b",
            )
        dark_token_blocks = re.findall(
            r':root\[data-theme="dark"\]\s*\{([^}]*)\}',
            css,
            re.DOTALL,
        )
        dark_tokens = dict(
            (
                f"{role}-{name}",
                value,
            )
            for role, name, value in re.findall(
                r"--theme-(background|text)-([0-9a-f]+):\s*(#[0-9a-fA-F]{6});",
                dark_token_blocks[-1],
            )
        )
        backgrounds = [
            value for name, value in dark_tokens.items() if name.startswith("background-")
        ]
        text_colors = [
            value for name, value in dark_tokens.items() if name.startswith("text-")
        ]

        def relative_luminance(color: str) -> float:
            channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
            linear = [
                channel / 12.92
                if channel <= 0.04045
                else ((channel + 0.055) / 1.055) ** 2.4
                for channel in channels
            ]
            return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

        def contrast_ratio(first: str, second: str) -> float:
            lighter, darker = sorted(
                (relative_luminance(first), relative_luminance(second)),
                reverse=True,
            )
            return (lighter + 0.05) / (darker + 0.05)

        self.assertTrue(backgrounds)
        self.assertTrue(text_colors)
        self.assertGreaterEqual(
            min(contrast_ratio(foreground, background)
                for foreground in text_colors
                for background in backgrounds),
            4.5,
        )

    def test_settlement_completion_routes_serve_the_dedicated_page(self) -> None:
        for path in ("/settlement-completion", "/demo/settlement-completion"):
            status, body = asyncio.run(request_app(path))
            self.assertEqual(status, 200)
            page = body.decode()
            self.assertIn('id="settlement-completion-page"', page)
            self.assertIn("Congratulations — you’re nearly done.", page)
            self.assertIn("Thanks for choosing Casework", page)
            self.assertIn("Findings and Conclusions About a Marriage", page)
            self.assertIn('id="settlement-response-accepted-file"', page)
            self.assertIn("initializeSettlementCompletionPage()", page)
            self.assertIn("settlement-completion-auth-content", page)
            self.assertIn("settlement-completion-demo-content", page)
            self.assertIn('id="settlement-completion-back-to-mediation"', page)
            self.assertIn('id="settlement-completion-back-to-cases"', page)
            self.assertIn(
                'id="settlement-completion-finalize" class="completion-primary" type="button" disabled',
                page,
            )
            self.assertIn('window.history.back()', page)
            self.assertIn("/offer-response/complete", page)
            self.assertNotIn("casework-demo-case-completed", page)
            self.assertIn("settlementCompletionFinalize.hidden = true;", page)
            self.assertIn("settlementCompletionBackToCases.hidden = true;", page)
            self.assertIn("settlementCompletionBackToMediation.href = demoAssetOverviewUrl();", page)
            self.assertNotIn("settlementCompletionBack.href", page)

        page = body.decode()
        self.assertIn(
            (
                "`/settlement-completion?case_id=${encodeURIComponent(caseId)}"
                "&selection_id=${encodeURIComponent(selectionId)}`"
            ),
            page,
        )
        self.assertIn("loadSettlementOfferResponse({ showWorkflow: false })", page)
        self.assertIn("settlementOfferResponseState?.sent_confirmed", page)

    def test_rejection_completion_routes_serve_the_dedicated_page(self) -> None:
        for path in ("/rejection-completion", "/demo/rejection-completion"):
            status, body = asyncio.run(request_app(path))
            self.assertEqual(status, 200)
            page = body.decode()
            self.assertIn('id="rejection-completion-page"', page)
            self.assertIn("did not produce an accepted agreement", page)
            self.assertIn('id="rejection-completion-back-to-cases"', page)

    def test_root_displays_mode_choices_and_authentication_gate(self) -> None:
        status, body = asyncio.run(request_app("/"))

        self.assertEqual(status, 200)
        page = body.decode()
        self.assertIn('id="signup-form"', page)
        self.assertIn('id="login-form"', page)
        self.assertIn('name="email" type="text" autocomplete="username"', page)
        self.assertIn('id="verify-form"', page)
        self.assertIn('href="#account">Sign up / Sign in', page)
        self.assertIn('id="demo1-entry" href="/demo/start?source=demo1">Demo 1 — Free</a>', page)
        self.assertIn('id="demo2-entry" href="/demo/start?source=demo2">Demo 2 — Essential</a>', page)
        self.assertEqual(page.count('class="nav-cta demo-entry"'), 2)
        self.assertNotIn('id="demo-choices"', page)
        self.assertNotIn('class="demo-quick-link"', page)
        self.assertNotIn("demo-landing-banner", page)
        self.assertNotIn("Continue as Free account", page)
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
        self.assertIn('id="case-create-dialog"', page)
        self.assertIn('id="demo-case-choice-dialog"', page)
        self.assertIn('id="demo-case-documents-link" href="/demo/documents"', page)
        self.assertIn('id="demo-case-wizard-link" href="/demo/wizard"', page)
        self.assertIn("I have documents", page)
        self.assertIn("Guide me step by step", page)
        self.assertIn('data-case-mode="upload"', page)
        self.assertIn('data-case-mode="wizard"', page)
        self.assertIn('id="materials-workflow"', page)
        self.assertIn('id="materials-file-input"', page)
        self.assertIn('id="google-drive-picker"', page)
        self.assertIn('id="dropbox-picker"', page)
        self.assertIn('id="materials-import"', page)
        self.assertIn('"/api/v1/materials/config"', page)
        self.assertIn("OCR is needed but not supported", page)
        self.assertIn("page_limit_exceeded", page)
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

    def test_demo_entry_routes_open_single_case_flows(self) -> None:
        legacy_entry_paths = (
            ("/demo/1", "/demo/start?source=demo1"),
            ("/demo/1/dashboard", "/demo/start?source=demo1"),
            ("/demo/2", "/demo/start?source=demo2"),
            ("/demo/2/dashboard", "/demo/start?source=demo2"),
            ("/demo/dashboard", "/demo/start?source=demo2"),
            ("/demo?source=demo1", "/demo/start?source=demo1"),
            ("/demo?source=demo2", "/demo/start?source=demo2"),
        )
        with TestClient(app, follow_redirects=False) as client:
            for path, target in legacy_entry_paths:
                response = client.get(path)
                self.assertEqual(response.status_code, 307)
                self.assertEqual(response.headers["location"], target)
            self.assertEqual(client.get("/demo/start?source=demo2").status_code, 200)
            self.assertEqual(client.get("/demo/start?source=invalid").status_code, 400)
            self.assertEqual(client.get("/demo?source=invalid").status_code, 400)

        paths = (
            "/demo/start?source=demo1",
            "/demo?source=demo2&demo_case_id=sample-case",
            "/demo?source=demo1&demo_case_id=demo-free-case",
            "/demo/start?source=demo2",
        )
        with TestClient(app) as client:
            responses = [client.get(path) for path in paths]

        self.assertEqual([response.status_code for response in responses], [200] * len(paths))
        start_page = responses[0].text
        page = responses[1].text
        self.assertIn('const demoStartMode = window.location.pathname === "/demo/start";', start_page)
        self.assertIn('const demoRoute = demoStartMode || demoMode || demoOnlyMode || demoSettlementCompletionMode || demoRejectionCompletionMode;', page)
        self.assertNotIn('id="demo-my-cases-link"', page)
        self.assertNotIn('id="demo-inactive-cases"', page)
        self.assertNotIn("Archived cases", page)
        self.assertNotIn("My cases", page)
        self.assertNotIn("demoActiveCaseLimit", page)
        self.assertNotIn("archiveDemoCase", page)
        self.assertNotIn("restoreDemoCase", page)
        self.assertIn('if (serialized === null) return null;', page)
        self.assertIn('workflow_mode: mode === "documents" ? "upload" : "wizard"', page)
        self.assertIn('function openDemoCaseChoiceDialog()', page)
        self.assertIn('const demoCaseStorageKey = `casework-demo-session-case:${demoSource}`', page)
        self.assertIn('const demoFilesStorageKey = `casework-demo-session-files:${demoSource}`', page)
        self.assertIn('demoCaseDocumentsLink.href = `/demo/documents?${query}`', page)
        self.assertIn('demoCaseWizardLink.href = `/demo/wizard?${query}`', page)
        self.assertIn('window.location.assign(demoAssetOverviewUrl(demoCurrentCaseId))', page)
        self.assertIn('const demoAttemptLimit = demoSource === "demo1" ? 1 : 3;', page)
        self.assertIn("window.sessionStorage.getItem(demoCaseStorageKey)", page)
        self.assertIn("window.sessionStorage.setItem(demoCaseStorageKey, JSON.stringify(data))", page)
        self.assertIn('if (demoStartMode && performance.getEntriesByType("navigation")[0]?.type !== "reload")', page)
        self.assertIn("window.sessionStorage.removeItem(demoCaseStorageKey)", page)
        self.assertIn("window.sessionStorage.removeItem(demoFilesStorageKey)", page)
        self.assertIn('if (!event.persisted) return;', page)
        self.assertIn("function continueSettlementDemoAttempt()", page)
        self.assertIn("settlementDemoAttemptOrdinal >= demoAttemptLimit", page)
        self.assertIn("demoCaseDocumentsLink.addEventListener(\"click\"", page)
        self.assertIn("demoCaseWizardLink.addEventListener(\"click\"", page)
        self.assertIn('demo:${demoSource}:${demoCurrentCaseId}', page)
        self.assertIn('document.body.dataset.demoPlan = demoSource === "demo2" ? "essential" : "free"', page)
        self.assertNotIn("casework-demo-case-completed", page)
        self.assertNotIn('id="demo-completed-case"', page)
        self.assertIn("} else if (demoStartMode) {", start_page)
        self.assertNotIn('if (demoCaseData && demoSource === "demo1") {', start_page)
        self.assertNotIn('if (existingCase && demoSource === "demo1") {', start_page)
        self.assertNotIn('if (current && demoSource === "demo1") {', start_page)
        self.assertIn("pendingDemoCase = existingCase || {", start_page)
        self.assertIn('encodeURIComponent(current?.id || pendingDemoCase.id)', start_page)
        self.assertLess(
            start_page.index('id="demo-case-choice-dialog"'),
            start_page.index('id="existing-cases"'),
        )
        self.assertIn(".dashboard-header[hidden] { display: none; }", start_page)

    def test_billing_data_loads_only_after_valid_dashboard_status(self) -> None:
        _, body = asyncio.run(request_app("/"))
        page = body.decode()

        self.assertEqual(page.count("void loadAttemptCreditPackages();"), 1)
        dashboard_status = page.split(
            "async function loadDashboardStatus(", 1
        )[1].split(
            "\n        }\n\n        buildAssetTimelineStops();", 1
        )[0]
        billing_load = dashboard_status.index("void loadAttemptCreditPackages();")
        for guard in ("response.status === 401", "if (!response.ok)", "!account"):
            self.assertLess(dashboard_status.index(guard), billing_load)

    def test_settlement_planner_is_case_scoped_and_consent_aware(self) -> None:
        status, body = asyncio.run(request_app("/"))

        self.assertEqual(status, 200)
        page = body.decode()
        self.assertIn('id="settlement-planner"', page)
        self.assertIn('id="settlement-consent"', page)
        self.assertIn('id="settlement-ledger-json"', page)
        self.assertIn('id="settlement-axes-json"', page)
        self.assertIn('id="settlement-scenarios-table"', page)
        self.assertIn('id="settlement-offer-download"', page)
        self.assertIn("View asset and event tracing detail", page)
        self.assertIn("consent can be revoked at any time", page.lower())
        self.assertIn("pending qualified counsel review", page.lower())
        self.assertIn("not legal advice or representation", page.lower())
        self.assertIn('id="settlement-export-confirmation"', page)
        self.assertIn('id="settlement-google-send"', page)
        self.assertIn('id="settlement-dropbox-send"', page)
        self.assertIn('id="settlement-email-send"', page)
        self.assertIn('settlementConsentRevoke.addEventListener("click", revokeSettlementConsent)', page)
        self.assertIn("openSettlementPlanner(item.id)", page)

    def test_existing_demo_shows_dynamic_fictional_settlement_scenarios(self) -> None:
        with TestClient(app) as client:
            response = client.get("/demo?source=demo2&demo_case_id=sample-case")
        status, body = response.status_code, response.content

        self.assertEqual(status, 200)
        page = body.decode()
        self.assertIn('id="settlement-scenarios-preview"', page)
        self.assertIn('<p class="eyebrow">Asset overview</p>', page)
        self.assertNotIn(">Demo preview<", page)
        self.assertGreater(
            page.index('id="settlement-scenarios-preview"'),
            page.index('id="asset-chart-heading"'),
        )
        self.assertNotIn("Possible discussion scenarios", page)
        table_section = page.split('id="settlement-scenarios-preview"', 1)[1].split(
            'id="settlement-scenario-status"', 1
        )[0]
        self.assertIn('<input id="settlement-start-date" type="date"', page)
        self.assertIn('<input id="settlement-end-date" type="date"', page)
        self.assertIn('id="settlement-date-range-overlay"', page)
        self.assertIn("Drag along the chart", page)
        self.assertIn('id="settlement-scenario-results" role="radiogroup"', table_section)
        self.assertIn('aria-label="Select a fictional settlement scenario"', table_section)
        self.assertIn('id="settlement-demo-docx-download"', table_section)
        self.assertIn('id="settlement-demo-xlsx-download"', table_section)
        self.assertIn('id="settlement-demo-response-preview"', table_section)
        self.assertIn('id="settlement-demo-mark-sent"', table_section)
        self.assertIn('id="settlement-demo-response-files"', table_section)
        self.assertIn('name="settlement-demo-response-outcome"', table_section)
        self.assertIn('id="settlement-demo-add-counteroffer"', page)
        self.assertIn('id="settlement-demo-response-next"', table_section)
        self.assertIn('class="existing-offer-panel" id="settlement-demo-counteroffer-panel"', page)
        self.assertIn(".existing-offer-panel[hidden] { display:none; }", page)
        self.assertGreater(
            page.index('id="settlement-demo-counteroffer-panel"'),
            page.index('id="settlement-demo-response-preview"'),
        )
        self.assertIn(
            'document.getElementById("settlement-demo-counteroffer-panel").hidden =\n'
            '              settlementDemoResponseOutcome !== "counteroffer";',
            page,
        )
        self.assertNotIn("First sample attempt", table_section)
        self.assertRegex(
            page,
            r'settlementDemoResponseNext\.disabled\s*=\s*settlementDemoResponseOutcome\s*!==\s*"accepted"',
        )
        self.assertIn(
            'id="settlement-demo-add-counteroffer" type="button" disabled hidden',
            page,
        )
        self.assertNotIn("Congratulations", table_section)
        self.assertIn('id="settlement-completion-demo-content"', page)
        self.assertIn('`/demo/settlement-completion?source=${demoSource}&demo_case_id=${encodeURIComponent(demoCurrentCaseId)}`', page)
        self.assertIn("fictional-final-cr2a-agreement.docx", table_section)
        self.assertIn('const demoAttemptLimit = demoSource === "demo1" ? 1 : 3;', page)
        self.assertIn("The Free demo allows one attempt.", page)
        self.assertIn("The Essential demo allows up to ${demoAttemptLimit} attempts.", page)
        self.assertNotIn('type="file"', table_section)
        self.assertIn('id="settlement-demo-counteroffer-file" type="file"', page)
        self.assertIn("it stays in this browser and is not sent or analyzed", table_section)
        self.assertIn('id="settlement-scenario-status" role="status"', page)
        self.assertIn("function renderDemoSettlementScenarios()", page)
        self.assertIn('{ label: "Higher proposed share", share: 55 }', page)
        self.assertIn('{ label: "Even proposed share", share: 50 }', page)
        self.assertIn('{ label: "Lower proposed share", share: 45 }', page)
        self.assertNotIn('id="settlement-demo-export-share"', page)
        self.assertNotIn("settlementDemoExportShare", page)
        self.assertIn('name = "settlement-demo-scenario"', page)
        self.assertIn("community_share_bps: settlementDemoSelectedShareBps", page)
        self.assertIn("settlementDemoResponseFiles.hidden = false", page)
        self.assertIn("settlementDemoResponseOutcome === \"counteroffer\"", page)
        self.assertIn("settlementDemoResponseOutcome === \"accepted\"", page)
        self.assertLess(
            table_section.index('id="settlement-scenario-results"'),
            table_section.index('id="settlement-demo-docx-download"'),
        )
        self.assertLess(
            page.index('id="settlement-demo-xlsx-download"'),
            page.index('id="settlement-scenario-status"'),
        )
        self.assertIn('assetTimelineChart.addEventListener("pointerdown"', page)
        self.assertIn('body[data-demo-page="settlement"] .scenario-disclaimer', page)
        self.assertIn("not necessarily a legal separation or characterization date", page)
        self.assertNotIn("<table", table_section)
        self.assertNotIn("<tbody", table_section)
        self.assertNotIn("81 combinations", page)
        self.assertNotIn("$500,000 on 2024-01-01", page)

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
        self.assertIn("renderAssetTimelineCursor(index, values)", page)
        self.assertIn("Scenario ideas for the selected dates", page)
        self.assertNotIn("Possible discussion scenarios", page)
        self.assertNotIn("scenarioOptions.addEventListener", page)
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
        self.assertIn("sampleAssetYears[stop.yearIndex][category] = values[category]", edit_logic)
        self.assertIn("interpolatedAssetOverrides.set(stop.date, values)", edit_logic)
        self.assertIn("renderAssetTimeline();", edit_logic)
        self.assertIn(
            "Unsaved edits canceled because you changed the selected timeline point.",
            edit_logic,
        )
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
        self.assertNotIn('id="asset-milestone-index"', page)
        self.assertNotIn("renderAssetMilestoneIndex", page)
        self.assertNotIn("assetMilestoneIndex", page)
        self.assertIn('assetMilestoneSelector.addEventListener("change"', page)
        self.assertIn('assetChartMilestones.addEventListener("click"', page)
        self.assertIn('assetChartMilestones.addEventListener("keydown"', page)
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
        self.assertIn("This date is outside the annual sample range", page)
        self.assertIn("selectAssetMilestone(marker.dataset.milestoneId)", page)
        milestone_logic = page.split(
            "function milestoneActiveDate(milestone)", 1
        )[1].split("function renderAssetSnapshot(index)", 1)[0]
        self.assertNotIn("fetch(", milestone_logic)
        self.assertNotIn("localStorage", milestone_logic)
        self.assertNotIn("sessionStorage", milestone_logic)

    def test_demo_documents_offer_requires_valid_details(self) -> None:
        with TestClient(app) as client:
            page = client.get("/demo/documents?source=demo2&demo_case_id=sample-case").text
        self.assertIn('id="demo-documents-has-offer" type="checkbox"', page)
        self.assertIn('id="demo-documents-offer-panel" aria-label="Existing offer" hidden', page)
        self.assertIn('id="demo-documents-offer-file" type="file"', page)
        self.assertIn('id="demo-documents-offer-notes"', page)
        self.assertNotIn('id="demo-documents-back"', page)
        self.assertIn('hasMinimumOfferNotes(demoDocumentsOfferNotes.value)', page)
        self.assertIn('demoSelectedFiles.length === 0 || demoDocumentsOfferBusy', page)
        self.assertIn('store.put(record)', page)
        self.assertIn('documents_offer: {', page)

    def test_asset_trend_uses_selector_without_duplicate_highlight_list(self) -> None:
        with TestClient(app) as client:
            response = client.get("/demo?source=demo2&demo_case_id=sample-case")
        status, body = response.status_code, response.content

        self.assertEqual(status, 200)
        page = body.decode()
        trend = page.split('id="asset-chart-heading"', 1)[1].split(
            'id="settlement-scenarios-preview"', 1
        )[0]
        self.assertIn('<label class="asset-milestone-field" for="asset-milestone-selector">Milestone to highlight', trend)
        self.assertIn('<select class="asset-milestone-select" id="asset-milestone-selector"', trend)
        self.assertIn('id="asset-milestone-status" role="status" aria-live="polite"', trend)
        self.assertIn('id="asset-chart-milestones"', trend)
        self.assertNotIn('id="asset-milestone-index"', trend)
        self.assertNotIn(">Highlight</button>", trend)
        self.assertIn("grid-template-columns: minmax(0, 1fr); max-width: 460px", page)

        selection_logic = page.split("function selectAssetMilestone(id)", 1)[1].split(
            "function updateAssetEditControls()", 1
        )[0]
        self.assertIn("assetMilestoneSelector.value = id;", selection_logic)
        self.assertIn("renderAssetTimeline();", selection_logic)
        self.assertIn("announceSelectedAssetMilestone();", selection_logic)

    def test_wizard_collects_acquisition_method_and_title_status(self) -> None:
        status, body = asyncio.run(request_app("/demo/wizard"))

        self.assertEqual(status, 200)
        page = body.decode()
        finance_markup = page.split("function renderWizardCollections()", 1)[1].split(
            "function renderWizardDraft()", 1
        )[0]
        self.assertIn('data-wizard-field="acquisitionMethod"', finance_markup)
        self.assertIn('value="purchase"', finance_markup)
        self.assertIn('value="inheritance"', finance_markup)
        self.assertIn('value="gift"', finance_markup)
        self.assertIn('value="pre_existing"', finance_markup)
        self.assertIn('data-wizard-field="holding"', finance_markup)
        self.assertIn('value="joint"', finance_markup)
        self.assertIn('value="individual"', finance_markup)

    def test_wizard_section_navigation_opens_an_editable_entry(self) -> None:
        status, body = asyncio.run(request_app("/demo/wizard"))

        self.assertEqual(status, 200)
        page = body.decode()
        for section_id in (
            "wizard-dates",
            "wizard-finances",
            "wizard-issues",
            "wizard-agreements",
            "wizard-review",
        ):
            self.assertIn(f'id="{section_id}" tabindex="-1"', page)

        navigation = page.split(
            "function handleWizardSectionNavigation(event)", 1
        )[1].split("function handleWizardCollectionClick", 1)[0]
        self.assertIn('a[href^="#wizard-"]', navigation)
        self.assertIn('"wizard-finances": "finances"', navigation)
        self.assertIn('"wizard-issues": "issues"', navigation)
        self.assertIn('"wizard-agreements": "agreements"', navigation)
        self.assertIn("wizardDraft[collection].length === 0", navigation)
        self.assertIn("addWizardEntry(collection)", navigation)
        self.assertIn('setAttribute("aria-current", "step")', navigation)
        self.assertIn("focusTarget.focus({ preventScroll: true })", navigation)

    def test_browser_local_ids_work_on_insecure_lan_http(self) -> None:
        status, body = asyncio.run(request_app("/demo/wizard"))

        self.assertEqual(status, 200)
        page = body.decode()
        id_generator = page.split("function createLocalId(prefix)", 1)[1].split(
            "function normalizeWizardDraft", 1
        )[0]
        self.assertIn("globalThis.crypto", id_generator)
        self.assertIn("webCrypto?.randomUUID", id_generator)
        self.assertIn("webCrypto?.getRandomValues", id_generator)
        self.assertIn("Math.random()", id_generator)
        self.assertNotIn("crypto.randomUUID()", id_generator)
        demo_case_creation = page.split("function openDemoCaseChoiceDialog()", 1)[1].split(
            "function startDemoCase", 1
        )[0]
        self.assertIn('createLocalId("case")', demo_case_creation)

    def test_wizard_supports_browser_local_optional_files_for_each_record(self) -> None:
        status, body = asyncio.run(request_app("/demo/wizard"))

        self.assertEqual(status, 200)
        page = body.decode()
        collection_renderer = page.split(
            "function renderWizardCollections()", 1
        )[1].split("function refreshWizardReview()", 1)[0]
        for collection in ("finances", "issues", "agreements"):
            self.assertIn(f'wizardAttachmentMarkup(entry, "{collection}")', collection_renderer)
        self.assertIn('type="file" multiple data-wizard-files="${collection}"', page)
        self.assertIn("stay in this browser only", page)
        self.assertIn("blob: file.slice(0, file.size, file.type)", page)
        self.assertIn("Evidence is not uploaded or analyzed.", page)

    def test_property_tracing_api_persists_case_facts_and_returns_candidates(self) -> None:
        case = SimpleNamespace(
            relationship_milestones={},
            property_assets=[],
            asset_liability_inventory={"legacy": "preserved"},
        )
        db = Mock()
        db.get.return_value = case
        payload = PropertyTracingUpdate.model_validate(
            {
                "relationship_milestones": {
                    "cohabitation_start_date": "2020-01-01",
                    "marriage_date": "2021-01-01",
                    "separation_start_date": "2025-01-01",
                    "divorce_filing_date": "2025-02-01",
                },
                "assets": [
                    {
                        "name": "Family home",
                        "acquisition_date": "2022-05-01",
                        "acquisition_method": "purchase",
                        "title_status": "joint",
                    }
                ],
            }
        )
        case_id = uuid4()

        updated = update_property_tracing(case_id, payload, db)
        read_back = read_property_tracing(case_id, db)

        self.assertEqual(
            case.relationship_milestones["cohabitation_start_date"],
            "2020-01-01",
        )
        self.assertEqual(case.property_assets[0]["acquisition_date"], "2022-05-01")
        self.assertEqual(case.asset_liability_inventory, {"legacy": "preserved"})
        self.assertEqual(updated.assets[0].classification, "community_property_candidate")
        self.assertEqual(read_back.assets[0].classification, "community_property_candidate")
        self.assertIn("not legal determinations", read_back.classification_notice)
        db.commit.assert_called_once()

    def test_asset_timeline_includes_chronological_milestone_stops(self) -> None:
        status, body = asyncio.run(request_app("/"))

        self.assertEqual(status, 200)
        page = body.decode()
        timeline_logic = page.split("function buildAssetTimelineStops", 1)[1].split(
            "function assetSnapshotAtDate", 1
        )[0]
        self.assertIn("assetYearStops.replaceChildren()", timeline_logic)
        self.assertIn("left.date.localeCompare(right.date)", timeline_logic)
        self.assertIn("assetYearStops.append(option)", timeline_logic)
        self.assertIn("selectedAssetYearIndex = assetTimelineStops.reduce", timeline_logic)
        self.assertIn("distance < nearestDistance ? index : nearestIndex", timeline_logic)
        self.assertIn("const fraction = (timestamp - startTimestamp)", page)
        self.assertIn("Math.round(value + (nextSample[category][partyIndex] - value) * fraction)", page)
        self.assertIn("if (timestamp < endTimestamp)", page)
        self.assertIn('values: assetSnapshotAtDate(stop.date).values', page)
        self.assertIn('xForDate(Date.parse(`${stop.date}T00:00:00Z`))', page)
        self.assertIn("const chartStart = Math.min(sampleStart, ...milestoneTimestamps)", page)
        self.assertIn("const chartEnd = Math.max(sampleEnd, ...milestoneTimestamps)", page)
        self.assertIn("buildAssetTimelineStops();\n        renderAssetMilestoneControls();", page)

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
            asyncio.run(request_app(f"/cases/{case_id}/property-tracing")),
            asyncio.run(
                request_app(
                    f"/cases/{case_id}/property-tracing",
                    "PUT",
                    b"{}",
                )
            ),
        )

        self.assertEqual(
            [status for status, _ in requests],
            [503, 503, 503, 503, 503, 503, 503, 503, 503, 503, 503, 503, 503, 503],
        )
        for _, body in requests:
            self.assertIn(b"Authentication is not configured", body)

    def test_document_deletion_removes_the_object_and_metadata(self) -> None:
        document_id = uuid4()
        user_id = uuid4()
        document = SimpleNamespace(id=document_id, case_id=uuid4(), object_key="case/document.pdf")
        user = SimpleNamespace(id=user_id)
        db = Mock()
        db.get.side_effect = [document, user]
        request = SimpleNamespace(state=SimpleNamespace(user_id=user_id))

        with (
            patch("app.main.delete_document_scope") as delete_scope,
            patch("app.main.scope_tombstone", return_value=None),
        ):
            response = delete_document(
                document_id,
                PermanentDeletionConfirmation(confirmation="DELETE MATERIAL"),
                request,
                db,
            )

        self.assertEqual(response.status_code, 204)
        self.assertEqual(response.headers["cache-control"], "no-store")
        delete_scope.assert_called_once()

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

    def test_document_deletion_reports_failure_from_permanent_deletion_service(self) -> None:
        user_id = uuid4()
        document = SimpleNamespace(id=uuid4(), case_id=uuid4(), object_key="case/document.pdf")
        user = SimpleNamespace(id=user_id)
        db = Mock()
        db.get.side_effect = [document, user]
        request = SimpleNamespace(state=SimpleNamespace(user_id=user_id))

        with (
            patch("app.main.delete_document_scope", side_effect=HTTPException(status_code=503)),
            patch("app.main.scope_tombstone", return_value=None),
            self.assertRaises(HTTPException) as raised,
        ):
            delete_document(
                document.id,
                PermanentDeletionConfirmation(confirmation="DELETE MATERIAL"),
                request,
                db,
            )

        self.assertEqual(raised.exception.status_code, 503)

    def test_document_deletion_requires_exact_confirmation(self) -> None:
        user_id = uuid4()
        document = SimpleNamespace(id=uuid4(), case_id=uuid4(), object_key="case/document.pdf")
        user = SimpleNamespace(id=user_id)
        db = Mock()
        db.get.side_effect = [document, user]
        request = SimpleNamespace(state=SimpleNamespace(user_id=user_id))

        with (
            patch("app.main.delete_document_scope") as delete_scope,
            patch("app.main.scope_tombstone", return_value=None),
            self.assertRaises(HTTPException) as raised,
        ):
            delete_document(
                document.id,
                PermanentDeletionConfirmation(confirmation="DELETE CASE"),
                request,
                db,
            )

        self.assertEqual(raised.exception.status_code, 422)
        delete_scope.assert_not_called()

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
            ("CLOSED", "owner", 409),
        ):
            with self.subTest(method=method, role=role):
                db = Mock()
                case = SimpleNamespace(
                    status="finalized" if method == "CLOSED" else "draft", closed_at=None
                )
                db.get.side_effect = lambda model, key: {
                    AuthSession: auth_session,
                    User: user,
                    Case: case,
                    Document: document,
                }.get(model)
                membership = (
                    SimpleNamespace(role=role, suspended_at=None)
                    if role is not None
                    else None
                )
                db.scalar.side_effect = [None, membership, None, None, None]
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
                    patch("app.main.scope_tombstone", return_value=None),
                    patch("app.main.delete_document_scope") as delete_scope,
                ):
                    object_storage.get.return_value = b"private"
                    path = {
                        "GET": f"/documents/{document_id}/download",
                        "STATUS": f"/cases/{case_id}/documents/{document_id}/extraction-status",
                    }.get(method, f"/documents/{document_id}")
                    request_method = {"STATUS": "GET", "CLOSED": "POST"}.get(method, method)
                    status, _ = asyncio.run(
                        request_app(
                            path,
                            request_method,
                            body=(
                                b'{"confirmation":"DELETE MATERIAL"}'
                                if request_method == "DELETE"
                                else b'{}'
                            ),
                            headers=[
                                (b"cookie", b"auth_access=test; auth_csrf=csrf"),
                                (b"x-csrf-token", b"csrf"),
                                (
                                    b"content-type",
                                    b"application/json",
                                ),
                            ],
                        )
                    )

                self.assertEqual(status, expected_status)
                if method == "DELETE" and role == "owner":
                    delete_scope.assert_called_once()
                elif method == "GET" and role == "viewer":
                    object_storage.get.assert_called_once_with("case/document.pdf")
                else:
                    delete_scope.assert_not_called()
                    object_storage.get.assert_not_called()
                app.dependency_overrides.clear()

    def test_demo_wizard_has_no_back_link_and_keeps_completion_navigation(self) -> None:
        with TestClient(app) as client:
            for source in ("demo1", "demo2"):
                page = client.get(f"/demo/wizard?source={source}&demo_case_id=sample").text
                self.assertNotIn('id="demo-wizard-back"', page)
                self.assertIn('id="wizard-finish" type="button" disabled', page)
                self.assertIn('#wizard-finish { cursor: pointer; }', page)
                self.assertIn('#wizard-finish:disabled { cursor: not-allowed; }', page)
                self.assertIn(
                    'window.location.assign(preparationCaseId ? "/#account" : demoAssetOverviewUrl(demoCurrentCaseId))',
                    page,
                )

    def test_onboarding_paths_serve_the_authenticated_preview_page(self) -> None:
        paths = (
            "/onboarding/upload",
            "/onboarding/wizard",
            "/demo?source=demo2&demo_case_id=sample-case",
            "/demo/files",
            "/demo/documents",
            "/demo/wizard",
        )
        with TestClient(app) as client:
            responses = [client.get(path) for path in paths]

        self.assertEqual([response.status_code for response in responses], [200, 200, 200, 200, 200, 200])
        for response in responses[:2]:
            page = response.text
            self.assertIn('id="account-dashboard"', page)
            self.assertIn('"/api/v1/dashboard/status"', page)
            self.assertIn('id="case-create-dialog"', page)
            self.assertIn('data-case-mode="upload"', page)
            self.assertIn('data-case-mode="wizard"', page)
            self.assertIn("Start a new case", page)
            self.assertNotIn("active_case_limit", page)
            self.assertIn("This preview does not accept or save case details or documents.", page)
        demo_page = responses[2].text
        self.assertIn('const demoMode = window.location.pathname === "/demo";', demo_page)
        self.assertIn("Review case details and settlement scenarios.", demo_page)
        self.assertIn('body[data-demo-page="settlement"] #preparation-title', demo_page)
        self.assertIn('body[data-demo-page="settlement"] #asset-analysis-back', demo_page)
        self.assertIn('showPreparation("demo");', demo_page)
        file_manager_page = responses[3].text
        self.assertIn('const demoFileManagerMode = window.location.pathname === "/demo/files";', file_manager_page)
        self.assertIn('id="demo-case-navigation"', file_manager_page)
        self.assertNotIn('id="demo-my-cases-link"', file_manager_page)
        self.assertIn('id="demo-mediation-link" class="demo-case-nav-link" href="/demo">Asset Overview</a>', file_manager_page)
        self.assertIn('id="demo-file-management-link" class="demo-case-nav-link" href="/demo/files">Case file management</a>', file_manager_page)
        self.assertEqual(len(re.findall(r'class="demo-case-nav-link"', file_manager_page)), 2)
        self.assertIn('id="demo-file-manager"', file_manager_page)
        self.assertIn('id="demo-case-files-input" type="file" accept=".pdf,.docx" multiple', file_manager_page)
        self.assertIn("File contents stay in this browser only and are not uploaded.", file_manager_page)
        self.assertIn('window.sessionStorage.setItem(demoFilesStorageKey, JSON.stringify(records))', file_manager_page)
        self.assertIn('store.index("caseId").getAll(demoCaseFilesCaseId)', file_manager_page)
        self.assertIn('store.add({', file_manager_page)
        self.assertIn('store.put({', file_manager_page)
        self.assertIn('store.delete(fileId)', file_manager_page)
        self.assertIn('download.dataset.demoFileAction = "download"', file_manager_page)
        self.assertIn('replace.dataset.demoFileAction = "replace"', file_manager_page)
        self.assertIn('remove.dataset.demoFileAction = "delete"', file_manager_page)
        self.assertIn('body[data-demo-page="files"] #account-dashboard > .dashboard-panel', file_manager_page)
        self.assertIn('@media (max-width: 600px)', file_manager_page)
        self.assertIn('body[data-demo-page="settlement"] #demo-back-to-account', file_manager_page)
        self.assertIn('class="back-to-account" id="demo-back-to-account"', file_manager_page)
        self.assertIn('body[data-demo-page="settlement"] #asset-analysis-back', file_manager_page)
        self.assertIn('body[data-demo-page="settlement"] .sample-analysis-notice', file_manager_page)
        self.assertIn('body[data-demo-page="settlement"] .scenario-disclaimer', file_manager_page)
        self.assertIn('@media (max-width: 360px)', file_manager_page)
        self.assertIn('demoMediationLink.setAttribute("aria-current", "page")', file_manager_page)
        self.assertIn('demoFileManagementLink.setAttribute("aria-current", "page")', file_manager_page)
        document_demo_page = responses[4].text
        self.assertIn('const demoDocumentsMode = window.location.pathname === "/demo/documents";', document_demo_page)
        self.assertIn('id="demo-file-input" type="file"', document_demo_page)
        self.assertIn('id="demo-files-next" type="button" disabled', document_demo_page)
        self.assertNotIn('id="demo-documents-back"', document_demo_page)
        self.assertIn('id="demo-documents-has-offer" type="checkbox"', document_demo_page)
        self.assertIn('id="demo-documents-offer-file" type="file"', document_demo_page)
        self.assertIn('id="demo-documents-offer-notes"', document_demo_page)
        self.assertIn('hasMinimumOfferNotes(demoDocumentsOfferNotes.value)', document_demo_page)
        self.assertIn("Only PDF and DOCX files are supported.", document_demo_page)
        self.assertIn('window.location.assign(demoAssetOverviewUrl(demoCurrentCaseId))', document_demo_page)
        wizard_demo_page = responses[5].text
        self.assertNotIn('id="demo-wizard-back"', wizard_demo_page)
        self.assertIn('demoSource === "demo1"', wizard_demo_page)
        self.assertIn('demoSource === "demo2"', wizard_demo_page)
        self.assertIn('const demoRoute = demoStartMode || demoMode || demoOnlyMode || demoSettlementCompletionMode || demoRejectionCompletionMode;', wizard_demo_page)
        self.assertIn('id="wizard-filed-question"', wizard_demo_page)
        self.assertIn('id="wizard-role-question" disabled', wizard_demo_page)
        self.assertIn(
            'id="wizard-unlock-status" role="status" aria-live="polite"',
            wizard_demo_page,
        )
        self.assertIn("answer Yes to the filed-case question, then choose your role", wizard_demo_page)
        self.assertIn("Your intake sections are open. Choose Dates, Finances, Issues, Agreements, or Review below.", wizard_demo_page)
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
        self.assertIn('id="wizard-finish" type="button" disabled>Save and view your case', wizard_demo_page)
        self.assertIn('indexedDB.open(wizardDatabaseName, wizardDatabaseVersion)', wizard_demo_page)
        self.assertIn('wizardDatabaseName = "casework-wizard-intake"', wizard_demo_page)
        self.assertIn("Demo draft saved for this session. Restarting the demo clears it.", wizard_demo_page)
        self.assertIn("Restored the draft and attached files saved in this browser.", wizard_demo_page)
        wizard_change_handler = wizard_demo_page.split(
            "function handleWizardChange(event)", 1
        )[1].split("function addWizardEntry", 1)[0]
        self.assertNotIn("fetch(", wizard_change_handler)
        self.assertNotIn("localStorage", wizard_change_handler)
        demo_bootstrap = demo_page.rsplit('if (demoMode) {', 1)[1].split(
            "} else {", 1
        )[0]
        self.assertNotIn("fetch(", demo_bootstrap)
        self.assertNotIn("loadDashboardStatus(", demo_bootstrap)


if __name__ == "__main__":
    unittest.main()
