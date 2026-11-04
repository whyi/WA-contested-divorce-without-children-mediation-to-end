import importlib.util
from pathlib import Path
import unittest
from unittest.mock import Mock, patch


MIGRATION_PATH = (
    Path(__file__).resolve().parents[1]
    / "migrations"
    / "versions"
    / "0010_settlement_offer_response.py"
)
MIGRATION_SPEC = importlib.util.spec_from_file_location(
    "settlement_offer_response_migration",
    MIGRATION_PATH,
)
if MIGRATION_SPEC is None or MIGRATION_SPEC.loader is None:
    raise RuntimeError(f"Unable to load migration at {MIGRATION_PATH}")

migration = importlib.util.module_from_spec(MIGRATION_SPEC)
MIGRATION_SPEC.loader.exec_module(migration)


class SettlementOfferResponseMigrationTests(unittest.TestCase):
    def test_revision_fits_alembic_version_column(self) -> None:
        self.assertLessEqual(len(migration.revision), 32)
        self.assertEqual(migration.down_revision, "0009_cr2a_property_exports")

    def test_upgrade_creates_response_records_and_attachments(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.upgrade()

        self.assertEqual(
            [call.args[0] for call in operations.create_table.call_args_list],
            ["settlement_offer_responses", "settlement_offer_response_attachments"],
        )
        self.assertEqual(operations.create_index.call_count, 6)
        partial_indexes = [
            call.kwargs.get("postgresql_where")
            for call in operations.create_index.call_args_list
            if call.kwargs.get("unique")
        ]
        self.assertEqual(len(partial_indexes), 2)
        attachment_table = operations.create_table.call_args_list[1]
        attachment_constraints = [
            item for item in attachment_table.args[1:] if hasattr(item, "sqltext")
        ]
        self.assertTrue(
            any("accepted_offer" in str(constraint.sqltext) for constraint in attachment_constraints)
        )

    def test_downgrade_removes_attachments_before_parent_records(self) -> None:
        operations = Mock()
        with patch.object(migration, "op", operations):
            migration.downgrade()

        self.assertEqual(
            [call.args[0] for call in operations.drop_table.call_args_list],
            ["settlement_offer_response_attachments", "settlement_offer_responses"],
        )


if __name__ == "__main__":
    unittest.main()
