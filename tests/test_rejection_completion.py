import re
import unittest
from pathlib import Path

PAGE = (Path(__file__).parents[1] / "src" / "app" / "static" / "index.html").read_text()
MAIN = (Path(__file__).parents[1] / "src" / "app" / "main.py").read_text()


class RejectionCompletionTests(unittest.TestCase):


    def test_next_attempt_is_user_initiated_and_demo_does_not_persist(self) -> None:
        self.assertIn("async function continueSettlementOfferResponse()", PAGE)
        next_attempt_handler = PAGE.split(
            'settlementResponseNextAttempt.addEventListener("click"', 1
        )[1].split('settlementResponseStop.addEventListener("click"', 1)[0]
        self.assertIn('settlementOfferResponseState?.outcome !== "rejected"', next_attempt_handler)
        self.assertIn("void continueSettlementOfferResponse()", next_attempt_handler)
        demo_stop_handler = PAGE[PAGE.index('settlementDemoStop.addEventListener("click"') :]
        demo_stop_handler = demo_stop_handler[: demo_stop_handler.index("\n        });") + len("\n        });")]
        self.assertIn("await showAppConfirm(", demo_stop_handler)
        self.assertIn(
            '`/demo/rejection-completion?source=${demoSource}&demo_case_id=${encodeURIComponent(demoCurrentCaseId)}`',
            demo_stop_handler,
        )
        self.assertNotIn("settlementApi(", demo_stop_handler)
        self.assertIn(
            "Stop this fictional workflow? No real case will be closed and no data will be saved.",
            demo_stop_handler,
        )

    def test_dedicated_authenticated_and_fictional_demo_routes_are_available(self) -> None:
        self.assertIn('@app.get("/rejection-completion"', MAIN)
        self.assertIn('"/demo/rejection-completion"', MAIN)
        self.assertIn('window.location.pathname === "/rejection-completion"', PAGE)
        self.assertIn('window.location.pathname === "/demo/rejection-completion"', PAGE)
        self.assertIn(
            '`/demo/rejection-completion?source=${demoSource}&demo_case_id=${encodeURIComponent(demoCurrentCaseId)}`',
            PAGE,
        )
        self.assertIn("no real case data was closed, changed, or saved", PAGE)

    def test_completion_page_is_neutral_accessible_and_distinguishes_product_closure(self) -> None:
        section = re.search(r'<section[^>]*id="rejection-completion-page"[^>]*>', PAGE)
        self.assertIsNotNone(section)
        self.assertIn('aria-labelledby="rejection-completion-title"', section.group(0))
        self.assertIn('id="rejection-completion-status" class="settlement-completion-status" role="status" aria-live="polite"', PAGE)
        for phrase in (
            "mediation did not produce an accepted agreement in this workflow",
            "does not resolve or end your divorce case",
            "does not file anything with a court",
            "does not delete data",
            "does not change your legal status",
            "discuss possible next steps with your mediator",
            "consult qualified Washington counsel",
            "learn about court processes",
            "This is not legal advice",
            "Back to your case",
        ):
            self.assertIn(phrase, PAGE)
        self.assertIn("data-rejection-completion-page", PAGE)
        self.assertIn('settlementApi("/api/v1/closed-cases")', PAGE)
        self.assertIn('closedCase.closed_reason !== "stopped"', PAGE)


if __name__ == "__main__":
    unittest.main()
