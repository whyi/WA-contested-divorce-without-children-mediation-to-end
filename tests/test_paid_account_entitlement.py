import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException
from fastapi.testclient import TestClient

from app import billing_routes
from app.auth_routes import require_current_user
from app.config import Settings
from app.database import get_db
from app.main import app
from app.models import DocumentCreditLedgerEntry, User


class PaidAccountEntitlementTests(unittest.TestCase):
    def tearDown(self) -> None:
        app.dependency_overrides.clear()

    def test_account_status_uses_purchase_history_not_remaining_balance(self) -> None:
        user = SimpleNamespace(id=uuid4())
        purchase = SimpleNamespace(id=uuid4(), delta=5, source_type="package_purchase")
        db = Mock()
        db.scalar.return_value = purchase.id
        case_with_depleted_credits = SimpleNamespace(attempt_credit_balance=0)

        result = billing_routes.read_account_entitlement(user, db)

        self.assertEqual(result.status, "paid")
        self.assertEqual(case_with_depleted_credits.attempt_credit_balance, 0)
        statement = str(db.scalar.call_args.args[0])
        self.assertIn("document_credit_ledger_entries.source_type = ", statement)
        self.assertIn("document_credit_ledger_entries.delta > ", statement)
        self.assertNotIn("attempt_credit_balance", statement)

    def test_account_without_purchase_history_is_free(self) -> None:
        user = SimpleNamespace(id=uuid4())
        db = Mock()
        db.scalar.return_value = None

        self.assertEqual(billing_routes.read_account_entitlement(user, db).status, "free")

    def test_free_account_transition_is_an_unchanged_no_op(self) -> None:
        user = SimpleNamespace(id=uuid4())
        db = Mock()
        db.scalar.side_effect = [user.id, None]

        self.assertEqual(billing_routes.reject_paid_account_downgrade(user, db), {"status": "free"})
        self.assertEqual(db.scalar.call_count, 2)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_entitlement_read_route_reports_server_purchase_history(self) -> None:
        user = SimpleNamespace(id=uuid4())
        db = Mock()
        db.scalar.return_value = uuid4()
        app.dependency_overrides[require_current_user] = lambda: user

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        response = TestClient(app).get("/api/billing/account/entitlement")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "paid"})

    def test_ui_reads_server_status_and_offers_no_free_downgrade(self) -> None:
        page = (
            Path(__file__).parents[1] / "src" / "app" / "static" / "index.html"
        ).read_text()

        self.assertIn('id="account-entitlement-status"', page)
        self.assertIn('fetch("/api/billing/account/entitlement"', page)
        self.assertIn("remains Paid after credits are used", page)
        self.assertIn("does not change case access or credit balances", page)
        self.assertNotIn(">Switch to Free</button>", page)
        self.assertNotIn("subscription_plan", page)

    def test_paid_downgrade_returns_safe_error_without_mutating_data(self) -> None:
        user = SimpleNamespace(id=uuid4())
        db = Mock()
        db.scalar.side_effect = [user.id, uuid4()]

        with self.assertRaises(HTTPException) as raised:
            billing_routes.reject_paid_account_downgrade(user, db)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertIn("cannot switch to Free", raised.exception.detail)
        self.assertIn("No entitlement, credits, or case access were changed", raised.exception.detail)
        self.assertIn("FOR UPDATE", str(db.scalar.call_args_list[0].args[0]))
        db.add.assert_not_called()
        db.delete.assert_not_called()
        db.commit.assert_not_called()

    def test_unauthenticated_downgrade_request_is_rejected(self) -> None:
        settings = Settings(
            auth_enabled=True,
            auth_jwt_secret="paid-entitlement-test-secret-long-enough",
        )
        with patch("app.auth_routes.get_settings", return_value=settings):
            response = TestClient(app).post("/api/billing/account/downgrade-to-free")

        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Authentication required.")

    def test_stale_client_free_state_cannot_override_verified_purchase(self) -> None:
        user = SimpleNamespace(id=uuid4())
        db = Mock()
        db.scalar.side_effect = [user.id, uuid4()]
        app.dependency_overrides[require_current_user] = lambda: user

        def override_db():
            yield db

        app.dependency_overrides[get_db] = override_db
        response = TestClient(app).post(
            "/api/billing/account/downgrade-to-free",
            json={"status": "free", "balance": 0},
        )

        self.assertEqual(response.status_code, 409)
        self.assertEqual(db.scalar.call_count, 2)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_concurrent_paid_downgrade_requests_remain_rejected(self) -> None:
        user = SimpleNamespace(id=uuid4())
        purchase_id = uuid4()
        row_lock = threading.Lock()

        class SerializedPurchaseDB:
            def scalar(self, statement):
                entity = statement.column_descriptions[0]["entity"]
                if entity is User:
                    row_lock.acquire()
                    return user.id
                if entity is DocumentCreditLedgerEntry:
                    result = purchase_id
                    row_lock.release()
                    return result
                raise AssertionError(f"Unexpected query: {statement}")

        db = SerializedPurchaseDB()

        def request_downgrade() -> int:
            try:
                billing_routes.reject_paid_account_downgrade(user, db)
            except HTTPException as error:
                return error.status_code
            return 200

        with ThreadPoolExecutor(max_workers=8) as executor:
            statuses = list(executor.map(lambda _: request_downgrade(), range(16)))

        self.assertEqual(statuses, [409] * 16)


if __name__ == "__main__":
    unittest.main()
