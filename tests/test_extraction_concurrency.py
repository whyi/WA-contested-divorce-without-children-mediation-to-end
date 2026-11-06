import os
import threading
import unittest
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from app.database import Base
from app.extraction import claim_next_extraction_job
from app.models import Case, Document, DocumentExtractionJob


POSTGRES_URL = os.environ.get("WA_TEST_POSTGRES_URL")


@unittest.skipUnless(
    POSTGRES_URL,
    "Set WA_TEST_POSTGRES_URL to a disposable PostgreSQL database to run concurrency tests.",
)
class PostgresExtractionConcurrencyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.schema = f"extraction_concurrency_{uuid4().hex[:12]}"
        admin = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
        with admin.connect() as connection:
            connection.exec_driver_sql(f'CREATE SCHEMA "{self.schema}"')
        admin.dispose()
        self.engine = create_engine(
            POSTGRES_URL, connect_args={"options": f"-csearch_path={self.schema}"}
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            case = Case(status="draft", metadata_json={})
            db.add(case)
            db.flush()
            for index in range(5):
                document = Document(
                    case_id=case.id,
                    object_key=f"{case.id}/concurrency-{index}.pdf",
                    extension="pdf",
                    media_type="application/pdf",
                    sha256=f"{index:064x}",
                    size_bytes=1,
                )
                db.add(document)
                db.flush()
                db.add(
                    DocumentExtractionJob(
                        document_id=document.id,
                        source_sha256=document.sha256,
                        request_id=uuid4(),
                        status="processing" if index < 2 else "queued",
                        attempts=1 if index < 2 else 0,
                        lease_token=uuid4() if index < 2 else None,
                        lease_expires_at=(
                            datetime.now(UTC) + timedelta(minutes=5)
                            if index < 2
                            else None
                        ),
                    )
                )
            db.commit()
            self.case_id = case.id

    def tearDown(self) -> None:
        self.engine.dispose()
        admin = create_engine(POSTGRES_URL, isolation_level="AUTOCOMMIT")
        with admin.connect() as connection:
            connection.exec_driver_sql(f'DROP SCHEMA "{self.schema}" CASCADE')
        admin.dispose()

    def test_parallel_claims_do_not_exceed_three_active_jobs_per_case(self) -> None:
        barrier = threading.Barrier(3, timeout=10)

        def claim():
            with Session(self.engine) as db:
                barrier.wait()
                return claim_next_extraction_job(db)

        with ThreadPoolExecutor(max_workers=3) as executor:
            leases = list(executor.map(lambda _: claim(), range(3)))

        self.assertEqual(sum(lease is not None for lease in leases), 1)
        with Session(self.engine) as db:
            active_jobs = db.scalar(
                select(func.count(DocumentExtractionJob.id))
                .join(Document, Document.id == DocumentExtractionJob.document_id)
                .where(
                    Document.case_id == self.case_id,
                    DocumentExtractionJob.status == "processing",
                )
            )
        self.assertEqual(active_jobs, 3)


if __name__ == "__main__":
    unittest.main()
