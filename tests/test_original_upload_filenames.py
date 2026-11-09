import importlib.util
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
from urllib.parse import quote
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, inspect, text

from app.main import download_document
from app.services import Artifact


class OriginalFilenameTests(unittest.TestCase):
    def test_download_header_preserves_exact_unicode_spaces_and_punctuation(self) -> None:
        name = "Original \uc790\ub8cc #1 (FINAL).pdf"
        document = SimpleNamespace(
            id=uuid4(), object_key="private/document.pdf", original_filename=name,
            extension="pdf", media_type="application/pdf",
        )
        with patch("app.main.get_document_or_none", return_value=document), patch("app.main.storage") as storage:
            storage.get.return_value = b"%PDF-test"
            response = download_document(document.id, Mock())
        self.assertEqual(response.headers["Content-Disposition"], f"attachment; filename*=UTF-8''{quote(name, safe='')}")
        self.assertEqual(response.body, b"%PDF-test")

    def test_generated_artifact_does_not_claim_an_original_upload_name(self) -> None:
        self.assertIsNone(Artifact(b"generated", "docx", "application/docx").original_filename)
        self.assertEqual(Artifact(b"uploaded", "pdf", "application/pdf", "Exact NAME.pdf").original_filename, "Exact NAME.pdf")

    def test_migration_preserves_legacy_rows_and_round_trips_new_columns(self) -> None:
        path = Path(__file__).parents[1] / "migrations/versions/0028_original_upload_filenames.py"
        spec = importlib.util.spec_from_file_location("filename_migration", path)
        if spec is None or spec.loader is None:
            self.fail("Filename migration could not be loaded.")
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        engine = create_engine("sqlite://")
        with engine.begin() as connection:
            connection.execute(text("CREATE TABLE documents (id TEXT PRIMARY KEY, case_id TEXT)"))
            connection.execute(text("INSERT INTO documents VALUES ('legacy', 'case')"))
            with patch.object(migration, "op", Operations(MigrationContext.configure(connection))):
                migration.upgrade()
                self.assertIsNone(connection.execute(text("SELECT original_filename FROM documents")).scalar())
                columns = {column["name"] for column in inspect(connection).get_columns("documents")}
                self.assertTrue({"original_filename", "overwrite_document_id"} <= columns)
                self.assertIn("ix_documents_case_filename", [index["name"] for index in inspect(connection).get_indexes("documents")])
                migration.downgrade()
                self.assertEqual(connection.execute(text("SELECT id FROM documents")).scalar(), "legacy")
                self.assertEqual({column["name"] for column in inspect(connection).get_columns("documents")}, {"id", "case_id"})
        engine.dispose()
