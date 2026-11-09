from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import unittest
from urllib.parse import parse_qs, urlparse
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from starlette.responses import Response

from app.export_integrations import (
    DRIVE_SCOPE,
    Provider,
    _authorization_url,
    _consume_challenge,
    _connection_result_page,
    _settings_ready,
    export_destinations,
    start_export_provider_connection,
)
from app.models import AuthChallenge
from app.secret_encryption import derive_encryption_key, encrypt_secret


class ExportIntegrationTests(unittest.TestCase):
    def test_connection_results_keep_header_and_footer_for_every_provider_and_outcome(self) -> None:
        providers: tuple[Provider, ...] = ("google_drive", "dropbox")
        for provider in providers:
            for connected in (True, False):
                with self.subTest(provider=provider, connected=connected):
                    response = _connection_result_page(provider, connected)
                    page = bytes(response.body).decode()
                    self.assertIn("<header>", page)
                    self.assertIn('aria-label="Casework home"', page)
                    self.assertIn("<footer>", page)
                    self.assertLess(page.index("<header>"), page.index("<main>"))
                    self.assertLess(page.index("</main>"), page.index("<footer>"))
                    self.assertIn("window.opener.postMessage", page)
                    self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_provider_setup_is_unavailable_for_demo_or_missing_encryption_key(self) -> None:
        settings = SimpleNamespace(
            auth_enabled=True,
            case_data_enabled=True,
            demo_mode_enabled=True,
            auth_encryption_key="encryption-test-secret-with-at-least-32-bytes",
            google_client_id="client",
            google_client_secret="secret",
            dropbox_app_key="key",
            dropbox_app_secret="secret",
        )
        with patch("app.export_integrations.get_settings", return_value=settings):
            self.assertFalse(_settings_ready("google_drive"))
            self.assertFalse(_settings_ready("dropbox"))

        settings.demo_mode_enabled = False
        settings.auth_encryption_key = None
        with patch("app.export_integrations.get_settings", return_value=settings):
            self.assertFalse(_settings_ready("google_drive"))

    def test_authorization_urls_request_minimal_scopes_and_pkce(self) -> None:
        settings = SimpleNamespace(
            google_client_id="google-client",
            dropbox_app_key="dropbox-key",
            auth_public_base_url="https://casework.example.test/",
        )
        verifier = "random-pkce-verifier"
        with patch("app.export_integrations.get_settings", return_value=settings):
            google = parse_qs(urlparse(_authorization_url("google_drive", "state", verifier)).query)
            dropbox = parse_qs(urlparse(_authorization_url("dropbox", "state", verifier)).query)

        self.assertIn(DRIVE_SCOPE, google["scope"][0].split())
        self.assertIn("email", google["scope"][0].split())
        self.assertEqual(google["code_challenge_method"], ["S256"])
        self.assertEqual(google["redirect_uri"], [
            "https://casework.example.test/api/export-integrations/google_drive/callback"
        ])
        self.assertIn("files.content.write", dropbox["scope"][0].split())
        self.assertIn("account_info.read", dropbox["scope"][0].split())
        self.assertEqual(dropbox["token_access_type"], ["offline"])
        self.assertEqual(dropbox["code_challenge_method"], ["S256"])

    def test_destination_status_is_user_scoped_uncached_and_configuration_aware(self) -> None:
        settings = SimpleNamespace(
            auth_enabled=True,
            case_data_enabled=True,
            demo_mode_enabled=False,
            auth_encryption_key="destination-test-secret-with-at-least-32-bytes",
            google_client_id="google-client",
            google_client_secret="google-secret",
            dropbox_app_key="dropbox-key",
            dropbox_app_secret="dropbox-secret",
            smtp_host="smtp.example.test",
            auth_email_from="casework@example.test",
        )
        db = Mock()
        db.scalars.return_value = []
        user = SimpleNamespace(id=uuid4())
        response = Response()

        with patch("app.export_integrations.get_settings", return_value=settings):
            destinations = export_destinations(user, db, response)

        self.assertTrue(destinations["google_drive"]["configured"])
        self.assertTrue(destinations["dropbox"]["configured"])
        self.assertTrue(destinations["email"]["configured"])
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_connect_persists_short_lived_pkce_state_and_disables_caching(self) -> None:
        from app.export_integrations import start_export_provider_connection

        user = SimpleNamespace(id=uuid4())
        db = Mock()
        response = Response()
        with (
            patch("app.export_integrations._settings_ready", return_value=True),
            patch("app.export_integrations._authorization_url", return_value="https://provider.test/auth"),
            patch("app.export_integrations.secrets.token_urlsafe", side_effect=["state", "verifier"]),
        ):
            result = start_export_provider_connection("google_drive", user, db, response)

        challenge = db.add.call_args.args[0]
        self.assertEqual(result["authorization_url"], "https://provider.test/auth")
        self.assertEqual(challenge.purpose, "export_google_drive")
        self.assertEqual(challenge.challenge, "state")
        self.assertEqual(challenge.context, {"code_verifier": "verifier"})
        self.assertEqual(response.headers["Cache-Control"], "no-store")

    def test_oauth_state_is_user_bound_and_consumed_once(self) -> None:
        user = SimpleNamespace(id=uuid4())
        challenge = AuthChallenge(
            user_id=user.id,
            purpose="export_google_drive",
            challenge="one-time-state",
            expires_at=datetime.now(UTC) + timedelta(minutes=5),
            context={"code_verifier": "pkce"},
        )
        db = Mock()
        db.scalar.return_value = challenge

        consumed = _consume_challenge(db, user, "google_drive", "one-time-state")
        self.assertIs(consumed, challenge)
        self.assertIsNotNone(challenge.consumed_at)

        db.scalar.return_value = None
        with self.assertRaises(HTTPException) as raised:
            _consume_challenge(db, user, "google_drive", "one-time-state")
        self.assertEqual(raised.exception.status_code, 401)

    def test_disconnect_removes_local_token_even_if_remote_revocation_fails(self) -> None:
        from app.export_integrations import disconnect_export_provider

        user = SimpleNamespace(id=uuid4())
        secret = "disconnect-test-secret-with-at-least-32-bytes"
        key = derive_encryption_key(secret)
        refresh_token = encrypt_secret(
            b"refresh-token",
            key,
            b"export:google_drive:" + str(user.id).encode() + b":refresh:v1",
        )
        connection = SimpleNamespace(
            provider="google_drive",
            encrypted_refresh_token=refresh_token,
            encrypted_access_token=b"",
        )
        db = Mock()
        db.scalar.return_value = connection
        settings = SimpleNamespace(auth_encryption_key=secret)

        with (
            patch("app.export_integrations.get_settings", return_value=settings),
            patch("app.export_integrations._revoke_provider_token", return_value=False) as revoke,
        ):
            response = Response()
            result = disconnect_export_provider("google_drive", user, db, response)

        self.assertEqual(result, {"disconnected": True, "provider_revoked": False})
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        revoke.assert_called_once_with("google_drive", "refresh-token")
        db.delete.assert_called_once_with(connection)
        db.commit.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
