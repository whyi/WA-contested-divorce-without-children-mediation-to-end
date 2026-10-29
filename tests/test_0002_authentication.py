import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch

import sqlalchemy as sa


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0002_authentication.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "authentication_migration", MIGRATION_PATH
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class AuthenticationMigrationTests(unittest.TestCase):
    def test_upgrade_creates_authentication_schema_and_downgrade_removes_it(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        table_calls = operations.create_table.call_args_list
        tables = {call.args[0]: call.args[1:] for call in table_calls}
        expected_tables = {
            "users",
            "external_identities",
            "auth_sessions",
            "refresh_tokens",
            "auth_tokens",
            "totp_credentials",
            "passkey_credentials",
            "auth_challenges",
            "recovery_codes",
            "auth_rate_limits",
            "auth_audit_events",
            "case_memberships",
        }
        self.assertEqual(set(tables), expected_tables)

        user_columns = {
            item.name: item
            for item in tables["users"]
            if isinstance(item, sa.Column)
        }
        self.assertFalse(user_columns["email"].nullable)
        self.assertTrue(user_columns["password_hash"].nullable)
        user_constraints = {
            item.name: item for item in tables["users"] if hasattr(item, "name")
        }
        self.assertIn("uq_users_email", user_constraints)
        self.assertIn("ck_users_status", user_constraints)

        membership_items = tables["case_memberships"]
        membership_constraints = {
            item.name: item for item in membership_items if hasattr(item, "name")
        }
        self.assertIn("uq_case_membership_user_case", membership_constraints)
        self.assertIn("ck_case_memberships_role", membership_constraints)
        membership_columns = {
            item.name: item
            for item in membership_items
            if isinstance(item, sa.Column)
        }
        self.assertEqual(
            {
                foreign_key.target_fullname: foreign_key.ondelete
                for column in membership_columns.values()
                for foreign_key in column.foreign_keys
            },
            {"cases.id": "CASCADE", "users.id": "CASCADE"},
        )

        created_indexes = {
            call.args[0]: (call.args[1], tuple(call.args[2]))
            for call in operations.create_index.call_args_list
        }
        self.assertEqual(
            created_indexes["ix_case_memberships_case_id"],
            ("case_memberships", ("case_id",)),
        )
        self.assertEqual(
            created_indexes["ix_case_memberships_user_id"],
            ("case_memberships", ("user_id",)),
        )

        operations.reset_mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()

        dropped_tables = [
            call.args[0] for call in operations.drop_table.call_args_list
        ]
        self.assertEqual(
            dropped_tables,
            [
                "case_memberships",
                "auth_audit_events",
                "auth_rate_limits",
                "recovery_codes",
                "auth_challenges",
                "passkey_credentials",
                "totp_credentials",
                "auth_tokens",
                "refresh_tokens",
                "auth_sessions",
                "external_identities",
                "users",
            ],
        )


if __name__ == "__main__":
    unittest.main()
