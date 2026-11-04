import unittest

from app.secret_encryption import decrypt_secret, derive_encryption_key, encrypt_secret


class SecretEncryptionTests(unittest.TestCase):
    def test_round_trip_and_associated_data_binding(self) -> None:
        key = derive_encryption_key("encryption-test-secret-with-at-least-32-bytes")
        ciphertext = encrypt_secret(b"provider-token", key, b"user-1:google:refresh")

        self.assertEqual(
            decrypt_secret(ciphertext, key, b"user-1:google:refresh"),
            b"provider-token",
        )
        with self.assertRaisesRegex(ValueError, "authenticated"):
            decrypt_secret(ciphertext, key, b"user-2:google:refresh")

    def test_rejects_short_keys_and_truncated_ciphertext(self) -> None:
        with self.assertRaisesRegex(ValueError, "at least 32 bytes"):
            derive_encryption_key("short")
        with self.assertRaisesRegex(ValueError, "invalid"):
            decrypt_secret(b"short", b"\0" * 32)


if __name__ == "__main__":
    unittest.main()
