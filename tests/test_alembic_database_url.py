import unittest
from types import SimpleNamespace

from alembic.config import Config

from app.database import alembic_option_value, widen_alembic_version_column


class AlembicDatabaseUrlTests(unittest.TestCase):
    def test_percent_encoded_credentials_round_trip_through_alembic_config(self) -> None:
        url = "postgresql+psycopg://user:p%40ss%2Fword@db.example.test:5432/app?sslmode=require"
        config = Config()

        config.set_main_option("sqlalchemy.url", alembic_option_value(url))

        self.assertEqual(config.get_main_option("sqlalchemy.url"), url)


class FakeConnection:
    def __init__(self, dialect_name: str) -> None:
        self.dialect = SimpleNamespace(name=dialect_name)
        self.statements: list[str] = []

    def exec_driver_sql(self, statement: str) -> None:
        self.statements.append(statement)


class AlembicVersionColumnTests(unittest.TestCase):
    def test_postgresql_version_column_is_widened_for_long_revision_ids(self) -> None:
        connection = FakeConnection("postgresql")

        widen_alembic_version_column(connection)  # type: ignore[arg-type]

        self.assertEqual(len(connection.statements), 2)
        self.assertIn("CREATE TABLE IF NOT EXISTS alembic_version", connection.statements[0])
        self.assertIn("TYPE VARCHAR(255)", connection.statements[1])

    def test_other_dialects_are_left_unchanged(self) -> None:
        connection = FakeConnection("sqlite")

        widen_alembic_version_column(connection)  # type: ignore[arg-type]

        self.assertEqual(connection.statements, [])


if __name__ == "__main__":
    unittest.main()
