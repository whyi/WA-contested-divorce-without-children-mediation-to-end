import unittest
from unittest.mock import Mock

from app.demo import (
    DEMO_EMAIL,
    DEMO_PASSWORD,
    DEMO_USER_ID,
    DEMO_USERNAME,
    ensure_demo_user,
    verify_demo_password,
)


class DemoAccountTests(unittest.TestCase):
    def test_demo_credentials_are_fixed_for_the_local_demo(self) -> None:
        self.assertEqual(DEMO_USERNAME, "demo")
        self.assertEqual(DEMO_PASSWORD, "demo")

    def test_seeds_an_active_email_verified_demo_user(self) -> None:
        db = Mock()
        db.scalar.return_value = None

        user = ensure_demo_user(db)

        self.assertEqual(user.id, DEMO_USER_ID)
        self.assertEqual(user.email, DEMO_EMAIL)
        self.assertEqual(user.status, "active")
        self.assertIsNotNone(user.email_verified_at)
        self.assertNotEqual(user.password_hash, DEMO_PASSWORD)
        self.assertTrue(verify_demo_password("demo", user.password_hash))
        db.add.assert_called_once_with(user)
        db.flush.assert_called_once_with()

    def test_rejects_wrong_demo_password(self) -> None:
        db = Mock()
        db.scalar.return_value = None
        user = ensure_demo_user(db)

        self.assertFalse(verify_demo_password("not-demo", user.password_hash))
        self.assertFalse(verify_demo_password("demo", None))


if __name__ == "__main__":
    unittest.main()
