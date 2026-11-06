import re
import unittest
from pathlib import Path

PAGE = (Path(__file__).parents[1] / "src" / "app" / "static" / "index.html").read_text()
MAIN = (Path(__file__).parents[1] / "src" / "app" / "main.py").read_text()


class RejectionCompletionTests(unittest.TestCase):
    def test_rejection_offers_explicit_continue_and_stop_choices(self) -> None:
        self.assertIn('id="settlement-response-next-attempt"', PAGE)
        self.assertIn(">Prepare another attempt</button>", PAGE)
        self.assertIn('id="settlement-response-stop"', PAGE)
        self.assertIn(">Stop mediation work and close this product case</button>", PAGE)
        self.assertIn("A new attempt is created only if you choose to continue.", PAGE)
        self.assertIn("finalization uses 1 attempt credit", PAGE)
        self.assertIn("current?.attempts_remaining != null", PAGE)

    def test_stop_requires_confirmation_and_closes_before_navigation(self) -> None:
        stop_handler = PAGE[PAGE.index("async function stopSettlementAfterRejection") :]
        stop_handler = stop_handler[: stop_handler.index("\n        async function ")]
        self.assertIn("window.confirm(", stop_handler)
        self.assertRegex(stop_handler, r"settlementApi\([\s\S]*?/close")
        self.assertIn('reason: "stopped"', stop_handler)
        self.assertLess(
            stop_handler.index("await settlementApi"),
            stop_handler.index("window.location.assign("),
        )
        self.assertIn("csrfHeaders()", PAGE)
        self.assertIn("The product workspace could not be closed", stop_handler)

    def test_next_attempt_is_user_initiated_and_demo_does_not_persist(self) -> None:
        self.assertIn('settlementResponseContinue.hidden = savedOutcome === "rejected"', PAGE)
        self.assertIn('settlementResponseNextAttempt.addEventListener("click"', PAGE)
        self.assertIn("void continueSettlementOfferResponse();", PAGE)
        self.assertNotIn('id="settlement-demo-stop"', PAGE)
        self.assertNotIn('settlementDemoStop.addEventListener', PAGE)
        self.assertIn('settlementDemoNextAttempt.addEventListener("click"', PAGE)

    def test_dedicated_authenticated_and_fictional_demo_routes_are_available(self) -> None:
        self.assertIn('@app.get("/rejection-completion"', MAIN)
        self.assertIn('"/demo/rejection-completion"', MAIN)
        self.assertIn('window.location.pathname === "/rejection-completion"', PAGE)
        self.assertIn('window.location.pathname === "/demo/rejection-completion"', PAGE)
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
