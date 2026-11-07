import logging
import time
from collections.abc import Callable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal
from app.deletion_ledger import reconcile_from_environment
from app.failure_logging import log_failure_event
from app.extraction import claim_next_extraction_job, process_extraction_job
from app.storage import ObjectStorage

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 2


def run_once(
    storage: ObjectStorage,
    session_factory: Callable[[], Session] = SessionLocal,
) -> bool:
    with session_factory() as db:
        lease = claim_next_extraction_job(db)
    if lease is None:
        return False

    with session_factory() as db:
        process_extraction_job(db, storage, lease)
    return True


def main() -> None:
    settings = get_settings()
    settings.require_owner_beta_readiness()
    storage = ObjectStorage(settings)
    if settings.case_data_enabled:
        reconcile_from_environment()
    while True:
        try:
            worked = run_once(storage)
        except SQLAlchemyError as error:
            log_failure_event(logger, "extraction_worker_database_failed", error)
            worked = False
        except Exception as error:
            log_failure_event(logger, "extraction_worker_iteration_failed", error)
            worked = False
        if not worked:
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
