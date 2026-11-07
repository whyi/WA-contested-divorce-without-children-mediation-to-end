from collections.abc import Generator

from sqlalchemy import Connection, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def alembic_option_value(value: str) -> str:
    # Alembic stores options through ConfigParser, which treats "%" as interpolation syntax.
    return value.replace("%", "%%")


def widen_alembic_version_column(connection: Connection) -> None:
    # Some revision IDs exceed Alembic's default 32-character version column on PostgreSQL.
    if connection.dialect.name != "postgresql":
        return
    connection.exec_driver_sql(
        "CREATE TABLE IF NOT EXISTS alembic_version ("
        "version_num VARCHAR(255) NOT NULL, "
        "CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num))"
    )
    connection.exec_driver_sql(
        "ALTER TABLE alembic_version ALTER COLUMN version_num TYPE VARCHAR(255)"
    )


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as session:
        yield session
