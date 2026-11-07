import smtplib
import unittest
from email.message import EmailMessage
from unittest.mock import MagicMock, patch

from app.config import Settings
from app.mail_delivery import send_smtp_message


class MailDeliveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.message = EmailMessage()
        self.message["To"] = "recipient@example.test"
        self.message["From"] = "casework@example.test"
        self.message["Subject"] = "Test message"
        self.message.set_content("Test body")

    def configured_settings(self, **overrides: object) -> Settings:
        options: dict[str, object] = {
            "smtp_host": "smtp.example.test",
            "auth_email_from": "casework@example.test",
        }
        options.update(overrides)
        return Settings(**options)

    def test_missing_smtp_host_or_sender_fails_before_connecting(self) -> None:
        for settings in (
            self.configured_settings(smtp_host=None),
            self.configured_settings(auth_email_from=None),
        ):
            with self.subTest(settings=settings):
                with (
                    patch("app.mail_delivery.smtplib.SMTP") as smtp,
                    self.assertRaisesRegex(RuntimeError, "Email delivery is not configured"),
                ):
                    send_smtp_message(self.message, settings)

                smtp.assert_not_called()

    def test_configured_delivery_uses_starttls_login_and_sends_message(self) -> None:
        settings = self.configured_settings(
            smtp_port=2525,
            smtp_username="mailer",
            smtp_password="mailer-password",
            smtp_starttls=True,
        )
        client = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = client
        smtp_context.__exit__.return_value = False

        with patch(
            "app.mail_delivery.smtplib.SMTP",
            return_value=smtp_context,
        ) as smtp:
            send_smtp_message(self.message, settings)

        smtp.assert_called_once_with("smtp.example.test", 2525, timeout=10)
        client.starttls.assert_called_once_with()
        client.login.assert_called_once_with("mailer", "mailer-password")
        client.send_message.assert_called_once_with(self.message)
        smtp_context.__exit__.assert_called_once_with(None, None, None)

    def test_default_settings_support_delivery_without_tls_or_authentication(self) -> None:
        settings = self.configured_settings(smtp_starttls=False)
        client = MagicMock()
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = client
        smtp_context.__exit__.return_value = False

        with (
            patch("app.mail_delivery.get_settings", return_value=settings) as get_settings,
            patch(
                "app.mail_delivery.smtplib.SMTP",
                return_value=smtp_context,
            ) as smtp,
        ):
            send_smtp_message(self.message)

        get_settings.assert_called_once_with()
        smtp.assert_called_once_with("smtp.example.test", 587, timeout=10)
        client.starttls.assert_not_called()
        client.login.assert_not_called()
        client.send_message.assert_called_once_with(self.message)

    def test_smtp_transport_errors_are_propagated(self) -> None:
        settings = self.configured_settings()
        client = MagicMock()
        client.send_message.side_effect = smtplib.SMTPException("delivery failed")
        smtp_context = MagicMock()
        smtp_context.__enter__.return_value = client
        smtp_context.__exit__.return_value = False

        with (
            patch("app.mail_delivery.smtplib.SMTP", return_value=smtp_context),
            self.assertRaisesRegex(smtplib.SMTPException, "delivery failed"),
        ):
            send_smtp_message(self.message, settings)

        smtp_context.__exit__.assert_called_once()


if __name__ == "__main__":
    unittest.main()
