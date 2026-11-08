import unittest

from fastapi import Response
from sqlalchemy import create_engine
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database import Base
from app.models import Case, CaseMembership, User
from app.settlement_routes import DocumentCreditBalanceRead, read_document_credit_balance, router


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


class DocumentCreditBalanceRouteTests(unittest.TestCase):
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
        self.db.add(self.owner)
        self.db.flush()
        self.case = Case(status="draft", metadata_json={})
        self.db.add(self.case)
        self.db.flush()
        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.owner.id, role="owner"))
        self.db.commit()

    def tearDown(self) -> None:
        self.db.close()
        for column, default in self._server_defaults:
            column.server_default = default

    def test_balance_is_declared_and_validated_with_a_model_that_accepts_the_package_list(self) -> None:
        route = next(
            item
            for item in router.routes
            if getattr(item, "path", "") == "/cases/{case_id}/settlement-planning/document-credits"
        )
        self.assertIs(route.response_model, DocumentCreditBalanceRead)

        response = Response()
        result = read_document_credit_balance(self.case.id, response, self.owner, self.db)

        self.assertEqual(
            DocumentCreditBalanceRead.model_validate(result.model_dump()).model_dump(),
            {
                "remaining": self.case.attempt_credit_balance,
                "free_first_finalization_available": True,
                "cost_per_finalization": 1,
                "package_sizes": [5, 10],
            },
        )
        self.assertEqual(response.headers["cache-control"], "no-store")


if __name__ == "__main__":
    unittest.main()
