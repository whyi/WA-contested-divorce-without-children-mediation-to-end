import logging
import time
from collections.abc import Callable

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.database import SessionLocal
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
    storage = ObjectStorage()
    while True:
        try:
            worked = run_once(storage)
        except SQLAlchemyError as error:
            logger.error("Extraction worker database operation failed (%s).", type(error).__name__)
            worked = False
        except Exception as error:
            logger.error("Extraction worker iteration failed (%s).", type(error).__name__)
            worked = False
        if not worked:
            time.sleep(POLL_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
