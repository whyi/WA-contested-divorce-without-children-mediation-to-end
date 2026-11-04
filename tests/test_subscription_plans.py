import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

from app.subscription_plans import PLANS, effective_plan_code, plan_for_user, user_settlement_attempt_limit


class SubscriptionPlanTests(unittest.TestCase):
    def test_plan_catalog_contains_expected_entitlements(self) -> None:
        self.assertEqual(
            [
                (
                    plan.code,
                    plan.active_case_limit,
                    plan.attempt_limit,
                    plan.monthly_document_credits,
                )
                for plan in PLANS
            ],
            [
                ("free", 1, 1, 0),
                ("essential", 3, 3, 2),
                ("plus", 10, 5, 5),
                ("pro", None, 10, 10),
            ],
        )

    def test_only_active_paid_subscriptions_receive_paid_entitlements(self) -> None:
        active = SimpleNamespace(
            subscription_plan="plus",
            subscription_status="active",
            subscription_period_end=datetime.now(UTC) + timedelta(days=1),
        )
        expired = SimpleNamespace(
            subscription_plan="plus",
            subscription_status="active",
            subscription_period_end=datetime.now(UTC) - timedelta(seconds=1),
        )
        canceled = SimpleNamespace(subscription_plan="pro", subscription_status="canceled")

        self.assertEqual(effective_plan_code(active), "plus")
        self.assertEqual(plan_for_user(active).attempt_limit, 5)
        self.assertEqual(effective_plan_code(expired), "free")
        self.assertEqual(effective_plan_code(canceled), "free")

    def test_legacy_limits_are_preserved_without_granting_new_plan_status(self) -> None:
        legacy = SimpleNamespace(
            subscription_plan="free",
            subscription_status="legacy",
            settlement_attempt_limit=5,
        )
        pre_membership = SimpleNamespace(settlement_attempt_limit=3)

        self.assertEqual(effective_plan_code(legacy), "plus")
        self.assertEqual(user_settlement_attempt_limit(legacy), 5)
        self.assertEqual(user_settlement_attempt_limit(pre_membership), 3)

    def test_unknown_plan_codes_fail_back_to_free_entitlements(self) -> None:
        user = SimpleNamespace(subscription_plan="unknown", subscription_status="active")

        self.assertEqual(effective_plan_code(user), "free")
        self.assertEqual(plan_for_user(user).active_case_limit, 1)


if __name__ == "__main__":
    unittest.main()
