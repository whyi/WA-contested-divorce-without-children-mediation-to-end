import unittest
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.main import WorkflowModeUpdate, update_case_workflow_mode
from app.models import Case, CaseMembership, User


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


class WorkflowModeUpdateTests(unittest.TestCase):
    def setUp(self) -> None:
        self._server_defaults = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                default = column.server_default
                if default is not None and "::" in str(getattr(default, "arg", "")):
                    self._server_defaults.append((column, default))
                    column.server_default = None
        engine = create_engine(
            "sqlite+pysqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.owner = User(email="owner@example.com", status="active")
        self.other = User(email="other@example.com", status="active")
        self.db.add_all([self.owner, self.other])
        self.db.flush()
        self.case = Case(
            status="draft",
            metadata_json={"case_title": "XYZ vs ABC", "workflow_mode": "wizard"},
        )
        self.db.add(self.case)
        self.db.flush()
        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.owner.id, role="owner"))
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        for column, default in self._server_defaults:
            column.server_default = default

    def test_owner_changes_the_start_path_and_keeps_other_metadata(self) -> None:
        result = update_case_workflow_mode(
            self.case.id, WorkflowModeUpdate(workflow_mode="upload"), self.owner, self.db
        )

        self.assertEqual(result.metadata_json["workflow_mode"], "upload")
        self.assertEqual(result.metadata_json["case_title"], "XYZ vs ABC")
        self.db.expire_all()
        self.assertEqual(self.db.get(Case, self.case.id).metadata_json["workflow_mode"], "upload")

    def test_account_without_membership_gets_not_found(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            update_case_workflow_mode(
                self.case.id, WorkflowModeUpdate(workflow_mode="upload"), self.other, self.db
            )

        self.assertEqual(caught.exception.status_code, 404)
        self.assertEqual(self.db.get(Case, self.case.id).metadata_json["workflow_mode"], "wizard")

    def test_non_owner_member_cannot_change_the_start_path(self) -> None:
        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.other.id, role="viewer"))
        self.db.commit()

        with self.assertRaises(HTTPException) as caught:
            update_case_workflow_mode(
                self.case.id, WorkflowModeUpdate(workflow_mode="upload"), self.other, self.db
            )

        self.assertEqual(caught.exception.status_code, 403)

    def test_unknown_case_is_not_found(self) -> None:
        with self.assertRaises(HTTPException) as caught:
            update_case_workflow_mode(
                uuid4(), WorkflowModeUpdate(workflow_mode="upload"), self.owner, self.db
            )

        self.assertEqual(caught.exception.status_code, 404)

    def test_only_known_paths_and_fields_are_accepted(self) -> None:
        with self.assertRaises(ValidationError):
            WorkflowModeUpdate(workflow_mode="mediation")
        with self.assertRaises(ValidationError):
            WorkflowModeUpdate.model_validate({"workflow_mode": "upload", "status": "closed"})

    def test_database_failure_is_retryable_and_rolled_back(self) -> None:
        with patch.object(self.db, "commit", side_effect=SQLAlchemyError("down")):
            with self.assertRaises(HTTPException) as caught:
                update_case_workflow_mode(
                    self.case.id, WorkflowModeUpdate(workflow_mode="upload"), self.owner, self.db
                )

        self.assertEqual(caught.exception.status_code, 503)
        self.db.expire_all()
        self.assertEqual(self.db.get(Case, self.case.id).metadata_json["workflow_mode"], "wizard")


if __name__ == "__main__":
    unittest.main()
