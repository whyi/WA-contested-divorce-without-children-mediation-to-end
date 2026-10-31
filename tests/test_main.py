import asyncio
import unittest
from uuid import uuid4

from app.main import app


async def request_app(
    path: str,
    method: str = "GET",
    body: bytes = b"",
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
        "headers": [],
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
        )

        self.assertEqual([status for status, _ in requests], [503, 503, 503])
        for _, body in requests:
            self.assertIn(b"Authentication is not configured", body)

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
