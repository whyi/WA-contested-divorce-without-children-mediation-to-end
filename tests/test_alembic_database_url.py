import unittest

from alembic.config import Config

from app.database import alembic_option_value


class AlembicDatabaseUrlTests(unittest.TestCase):
    def test_percent_encoded_credentials_round_trip_through_alembic_config(self) -> None:
        url = "postgresql+psycopg://user:p%40ss%2Fword@db.example.test:5432/app?sslmode=require"
        config = Config()

        config.set_main_option("sqlalchemy.url", alembic_option_value(url))

        self.assertEqual(config.get_main_option("sqlalchemy.url"), url)


if __name__ == "__main__":
    unittest.main()
