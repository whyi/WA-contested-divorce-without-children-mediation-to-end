import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from app.auth_routes import SignupRequest
from app.case_access import resolve_case_access
from app.case_limits import require_active_case_slot
from app.main import app

ROOT = Path(__file__).parents[1]
PAGE = (ROOT / "src" / "app" / "static" / "index.html").read_text(encoding="utf-8")
MIGRATION = ROOT / "migrations" / "versions" / "0027_single_general_account.py"


def _load_migration():
    spec = importlib.util.spec_from_file_location("migration_0027", MIGRATION)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SingleGeneralAccountTests(unittest.TestCase):
    def test_signup_has_no_account_type_choice(self) -> None:
        self.assertNotIn("account_type", SignupRequest.model_fields)
        self.assertNotIn("signup-account-type", PAGE)

    def test_delegation_routes_are_removed(self) -> None:
        paths = [getattr(route, "path", "") for route in app.routes]
        self.assertFalse([path for path in paths if "delegation" in path])

    def test_page_does_not_mention_professionals_or_delegation(self) -> None:
        lowered = PAGE.casefold()
        for term in ("attorney", "paralegal", "professional", "delegat"):
            self.assertNotIn(term, lowered)

    def test_case_access_requires_an_unrevoked_membership(self) -> None:
        membership = SimpleNamespace(role="owner")
        db = Mock()
        db.scalar.return_value = membership
        self.assertIs(resolve_case_access(db, uuid4(), uuid4()), membership)

        statement = str(db.scalar.call_args.args[0])
        self.assertIn("case_memberships.case_id", statement)
        self.assertIn("case_memberships.user_id", statement)
        self.assertIn("case_memberships.revoked_at IS NULL", statement)

        db.scalar.return_value = None
        self.assertIsNone(resolve_case_access(db, uuid4(), uuid4()))

    def test_every_active_account_gets_the_same_case_slot_rules(self) -> None:
        legacy_professional = SimpleNamespace(id=uuid4(), status="active", account_type="professional")
        db = Mock()
        db.get.return_value = legacy_professional
        db.scalar.return_value = 0
        with patch("app.case_limits.require_scope_active"):
            self.assertIs(require_active_case_slot(db, legacy_professional.id), legacy_professional)

    def test_second_case_is_refused_with_general_account_wording(self) -> None:
        user = SimpleNamespace(id=uuid4(), status="active")
        db = Mock()
        db.get.return_value = user
        db.scalar.return_value = 1
        with patch("app.case_limits.require_scope_active"):
            with self.assertRaises(Exception) as caught:
                require_active_case_slot(db, user.id)
        detail = str(getattr(caught.exception, "detail", ""))
        self.assertIn("An account can own one divorce case", detail)
        self.assertNotIn("professional", detail.casefold())


class SingleGeneralAccountMigrationTests(unittest.TestCase):
    def test_migration_restores_owners_after_revoking_delegates(self) -> None:
        module = _load_migration()
        self.assertEqual(module.revision, "0027_single_general_account")
        self.assertEqual(module.down_revision, "0026_owner_beta_fixture_registry")
        with patch.object(module, "op") as op:
            module.upgrade()
        statements = [str(call.args[0]) for call in op.execute.call_args_list]
        self.assertEqual(len(statements), 4)
        revoke_delegates = next(i for i, sql in enumerate(statements) if "role = 'delegate'" in sql)
        unsuspend = next(i for i, sql in enumerate(statements) if "suspended_at = NULL" in sql)
        self.assertLess(revoke_delegates, unsuspend)
        self.assertTrue(any("case_delegation_invitations" in sql and "'revoked'" in sql for sql in statements))
        self.assertTrue(any("account_type = 'party'" in sql for sql in statements))

    def test_migration_does_not_change_the_schema(self) -> None:
        module = _load_migration()
        with patch.object(module, "op") as op:
            module.upgrade()
            module.downgrade()
        for name in ("add_column", "drop_column", "create_table", "drop_table", "drop_constraint"):
            getattr(op, name).assert_not_called()


if __name__ == "__main__":
    unittest.main()
