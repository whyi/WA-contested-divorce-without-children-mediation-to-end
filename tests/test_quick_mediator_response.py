import re
import unittest
from pathlib import Path

from app.counteroffer import DELIVERY_BOUNDARY

ROOT = Path(__file__).parents[1]
PAGE = (ROOT / "src" / "app" / "static" / "index.html").read_text()
SOURCES = {p.name: p.read_text() for p in (ROOT / "src" / "app").glob("*.py")}


class QuickMediatorResponseTests(unittest.TestCase):


    def test_response_is_user_reported_and_never_delivered_or_verified(self) -> None:
        self.assertEqual(DELIVERY_BOUNDARY["recipient"], "mediator")
        self.assertFalse(DELIVERY_BOUNDARY["delivery_verified_by_app"])
        self.assertFalse(DELIVERY_BOUNDARY["response_verified_by_app"])
        self.assertEqual(DELIVERY_BOUNDARY["basis"], "user_reported")
        self.assertNotIn('id="settlement-response-workflow"', PAGE)
        self.assertIn("does not automatically deliver proposals", PAGE)


    def test_no_scheduler_reminder_or_outcome_inference_in_source(self) -> None:
        for name, text in SOURCES.items():
            lowered = text.lower()
            for marker in ("apscheduler", "celery", "backgroundtasks", "remind", "follow_up", "followup"):
                self.assertNotIn(marker, lowered, f"{name} contains {marker}")
        outcome_source = SOURCES["offer_response.py"]
        self.assertNotRegex(outcome_source, r"timedelta|utcnow\(\)\s*-|\.days\b")
        self.assertIsNone(re.search(r'"/[^"]*(remind|follow-?up|nudge)', SOURCES["main.py"], re.I))


if __name__ == "__main__":
    unittest.main()
