import json
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from uuid import uuid4

import httpx

from app.export_delivery import (
    ExportDeliveryError,
    ExportFile,
    _send_email,
    _token_aad,
    _upload_dropbox,
    _upload_google_drive,
    deliver_export_files,
)
from app.secret_encryption import derive_encryption_key, encrypt_secret


class ExportDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.settings = SimpleNamespace(
            auth_encryption_key="export-delivery-test-secret-with-at-least-32-bytes",
            google_client_id="google-client",
            google_client_secret="google-secret",
            dropbox_app_key="dropbox-key",
            dropbox_app_secret="dropbox-secret",
            auth_email_from="casework@example.test",
            smtp_host="smtp.example.test",
        )
        self.export = ExportFile("proposal.docx", "application/vnd.test", b"private document")

    def test_google_upload_uses_private_multipart_upload(self) -> None:
        response = Mock()
        with patch("app.export_delivery.httpx.post", return_value=response) as post:
            _upload_google_drive("provider-token", self.export)

        response.raise_for_status.assert_called_once_with()
        request = post.call_args.kwargs
        self.assertIn("uploadType", post.call_args.kwargs["params"])
        self.assertEqual(request["headers"]["Authorization"], "Bearer provider-token")
        self.assertIn("proposal.docx", request["content"].decode())
        self.assertNotIn("permissions", request["content"].decode())

    def test_dropbox_upload_targets_the_private_app_folder_without_a_share_link(self) -> None:
        response = Mock()
        with patch("app.export_delivery.httpx.post", return_value=response) as post:
            _upload_dropbox("provider-token", self.export)

        response.raise_for_status.assert_called_once_with()
        request = post.call_args.kwargs
        self.assertEqual(request["headers"]["Authorization"], "Bearer provider-token")
        upload_metadata = json.loads(request["headers"]["Dropbox-API-Arg"])
        self.assertEqual(upload_metadata["path"], "/proposal.docx")
        self.assertFalse(upload_metadata["autorename"])
        self.assertNotIn("shared_link", upload_metadata)

    def test_email_contains_both_requested_attachments(self) -> None:
        exports = [
            self.export,
            ExportFile("schedule.xlsx", "application/vnd.test", b"private workbook"),
        ]
        with (
            patch("app.export_delivery.get_settings", return_value=self.settings),
            patch("app.export_delivery.send_smtp_message") as send_message,
        ):
            _send_email("recipient@example.com", exports)

        message = send_message.call_args.args[0]
        self.assertEqual(message["To"], "recipient@example.com")
        self.assertEqual(
            [part.get_filename() for part in message.iter_attachments()],
            ["proposal.docx", "schedule.xlsx"],
        )

    def test_second_provider_upload_failure_reports_partial_delivery(self) -> None:
        user = SimpleNamespace(id=uuid4())
        key = derive_encryption_key(self.settings.auth_encryption_key)
        connection = SimpleNamespace(
            provider="google_drive",
            encrypted_access_token=encrypt_secret(
                b"access-token",
                key,
                _token_aad("google_drive", user.id, "access"),
            ),
            token_expires_at=datetime.now(UTC) + timedelta(hours=1),
        )
        db = Mock()
        db.scalar.return_value = connection
        exports = [self.export, ExportFile("schedule.xlsx", "application/vnd.test", b"workbook")]
        request_error = httpx.RequestError("network failure")

        with (
            patch("app.export_delivery.get_settings", return_value=self.settings),
            patch(
                "app.export_delivery._upload_google_drive",
                side_effect=[None, request_error],
            ),
            self.assertRaises(ExportDeliveryError) as raised,
        ):
            deliver_export_files(db, user, "google_drive", "", exports)

        self.assertEqual(raised.exception.delivered_files, 1)
        self.assertIn("uploaded 1 of 2 files", str(raised.exception))


if __name__ == "__main__":
    unittest.main()
