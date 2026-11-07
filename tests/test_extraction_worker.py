import unittest
from unittest.mock import MagicMock, Mock, patch
from uuid import uuid4

from app.extraction import ExtractionLease
from app.config import Settings
from app.extraction_worker import main, run_once


class ExtractionWorkerTests(unittest.TestCase):
    def test_worker_does_not_start_before_owner_beta_is_ready(self) -> None:
        with (
            patch(
                "app.extraction_worker.get_settings",
                return_value=Settings(owner_beta_readiness_required=True),
            ),
            patch("app.extraction_worker.ObjectStorage") as storage,
            self.assertRaisesRegex(RuntimeError, "owner_beta_mode_disabled"),
        ):
            main()

        storage.assert_not_called()

    def test_worker_processes_one_claimed_job_in_a_separate_session(self) -> None:
        storage = Mock()
        lease = ExtractionLease(uuid4(), uuid4())
        claim_db = MagicMock()
        process_db = MagicMock()
        claim_context = MagicMock()
        process_context = MagicMock()
        claim_context.__enter__.return_value = claim_db
        process_context.__enter__.return_value = process_db
        session_factory = Mock(side_effect=[claim_context, process_context])

        with (
            patch("app.extraction_worker.claim_next_extraction_job", return_value=lease),
            patch("app.extraction_worker.process_extraction_job") as process,
        ):
            did_work = run_once(storage, session_factory)

        self.assertTrue(did_work)
        process.assert_called_once_with(process_db, storage, lease)
        self.assertEqual(session_factory.call_count, 2)

    def test_worker_waits_when_no_jobs_are_queued(self) -> None:
        storage = Mock()
        session = MagicMock()
        session_context = MagicMock()
        session_context.__enter__.return_value = session
        session_factory = Mock(return_value=session_context)

        with patch("app.extraction_worker.claim_next_extraction_job", return_value=None):
            did_work = run_once(storage, session_factory)

        self.assertFalse(did_work)
        self.assertEqual(session_factory.call_count, 1)


if __name__ == "__main__":
    unittest.main()
