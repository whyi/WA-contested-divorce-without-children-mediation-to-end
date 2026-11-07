import json
import sys
from pathlib import Path
from typing import Any
from urllib.parse import quote


def build_database_url(
    secret: dict[str, Any],
    endpoint: dict[str, Any],
    database: str,
) -> str:
    username = secret.get("username")
    password = secret.get("password")
    host = endpoint.get("Address")
    port = endpoint.get("Port")

    if not isinstance(username, str) or not username:
        raise ValueError("RDS master secret is missing a username.")
    if not isinstance(password, str) or not password:
        raise ValueError("RDS master secret is missing a password.")
    if not isinstance(host, str) or not host:
        raise ValueError("RDS instance endpoint is not available.")
    if not isinstance(port, int) or not 1 <= port <= 65535:
        raise ValueError("RDS instance endpoint has an invalid port.")
    if not database:
        raise ValueError("UAT database name is empty.")

    return (
        f"postgresql+psycopg://{quote(username, safe='')}:"
        f"{quote(password, safe='')}@{host}:{port}/{quote(database, safe='')}"
        "?sslmode=require"
    )


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 4:
        print(
            "Usage: database_url.py RDS_SECRET_JSON ENDPOINT_JSON DATABASE OUTPUT",
            file=sys.stderr,
        )
        return 2

    secret_path, endpoint_path, database, output_path = args
    with Path(secret_path).open(encoding="utf-8") as secret_file:
        secret = json.load(secret_file)
    with Path(endpoint_path).open(encoding="utf-8") as endpoint_file:
        endpoint = json.load(endpoint_file)

    try:
        database_url = build_database_url(secret, endpoint, database)
    except ValueError as exc:
        print(f"Could not construct UAT database URL: {exc}", file=sys.stderr)
        return 1

    with Path(output_path).open("w", encoding="utf-8") as output_file:
        output_file.write(database_url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
