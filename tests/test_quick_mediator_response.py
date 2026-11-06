import re
import unittest
from pathlib import Path

from app.counteroffer import DELIVERY_BOUNDARY

ROOT = Path(__file__).parents[1]
PAGE = (ROOT / "src" / "app" / "static" / "index.html").read_text()
SOURCES = {p.name: p.read_text() for p in (ROOT / "src" / "app").glob("*.py")}


class QuickMediatorResponseTests(unittest.TestCase):
    def test_response_entry_follows_sent_confirmation_only(self) -> None:
        self.assertIn("What response did you receive?", PAGE)
        self.assertRegex(
            PAGE,
            r'settlement-response-outcome-fieldset"\)\.disabled =\s*!current\?\.sent_confirmed \|\| settlementResponseUploading \|\| frozen;',
        )
        for outcome in ("counteroffer", "rejected", "accepted"):
            self.assertIn(f'name="settlement-response-outcome" value="{outcome}"', PAGE)

    def test_response_is_user_reported_and_never_delivered_or_verified(self) -> None:
        self.assertEqual(DELIVERY_BOUNDARY["recipient"], "mediator")
        self.assertFalse(DELIVERY_BOUNDARY["delivery_verified_by_app"])
        self.assertFalse(DELIVERY_BOUNDARY["response_verified_by_app"])
        self.assertEqual(DELIVERY_BOUNDARY["basis"], "user_reported")
        self.assertIn("cannot confirm delivery or the response", PAGE)
        self.assertIn("This tracker does not send documents or call AI.", PAGE)

    def test_no_waiting_reminder_or_time_inference_ui(self) -> None:
        section = PAGE[PAGE.index('id="settlement-response-workflow"') :]
        section = section[: section.index("</section>\n")]
        for word in ("remind", "follow-up", "follow up", "weeks", "waiting for", "no response yet", "overdue"):
            self.assertNotIn(word, section.lower())

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
