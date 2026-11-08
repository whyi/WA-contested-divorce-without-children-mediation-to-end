import unittest
from html.parser import HTMLParser
from pathlib import Path


PAGE = (Path(__file__).parents[1] / "src/app/static/index.html").read_text(encoding="utf-8")


class WorkspaceMarkup(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.stack: list[tuple[str, dict[str, str | None]]] = []
        self.elements: dict[str, list[tuple[str, dict[str, str | None]]]] = {}

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        attributes = dict(attrs)
        node = (tag, attributes)
        if "id" in attributes:
            self.elements[str(attributes["id"])] = [*self.stack, node]
        if tag not in {"input", "meta", "link", "img", "br", "hr", "source", "area", "base", "embed", "param", "track", "wbr"}:
            self.stack.append(node)

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, -1, -1):
            if self.stack[index][0] == tag:
                del self.stack[index:]
                break


class AttemptWorkspaceEntryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.markup = WorkspaceMarkup()
        self.markup.feed(PAGE)

    def test_workspace_title_and_closed_optional_sections(self) -> None:
        self.assertIn('id="settlement-planner-title">Negotiation attempts</h2>', PAGE)
        for element_id in ("settlement-review-information", "settlement-evidence-tools", "settlement-scenario-assumptions"):
            tag, attrs = self.markup.elements[element_id][-1]
            self.assertEqual(tag, "details")
            self.assertNotIn("open", attrs)

    def test_legacy_controls_are_inside_collapsed_evidence_tools(self) -> None:
        for element_id in ("settlement-consent", "settlement-active-facts", "settlement-ledger-json", "settlement-ledger-add"):
            ancestors = self.markup.elements[element_id][:-1]
            self.assertTrue(any(attrs.get("id") == "settlement-evidence-tools" for _, attrs in ancestors))

    def test_attempt_work_remains_outside_collapsed_tools(self) -> None:
        for element_id in ("settlement-attempt-progress-list", "settlement-generate", "settlement-scenarios-table", "settlement-offer"):
            ancestors = self.markup.elements[element_id][:-1]
            self.assertFalse(any(attrs.get("id") in {"settlement-evidence-tools", "settlement-scenario-assumptions"} for _, attrs in ancestors))

    def test_startup_messages_are_actionable_not_revision_diagnostics(self) -> None:
        loader = PAGE.split("async function openSettlementPlanner(caseId)", 1)[1].split(
            "function renderSettlementFacts()", 1
        )[0]
        self.assertIn('"Loading your attempt workspace…"', loader)
        self.assertIn('"Attempt workspace ready. Calculate scenarios, then select one to prepare your proposal."', loader)
        self.assertNotIn("append-only ledger event(s) saved", loader)
        self.assertNotIn("state.profile_revision", loader)
        self.assertRegex(loader, r"setSettlementStatus\(\s*error instanceof Error")

    def test_assumptions_and_disclosures_are_preserved(self) -> None:
        ancestors = self.markup.elements["settlement-axes-json"][:-1]
        self.assertTrue(any(attrs.get("id") == "settlement-scenario-assumptions" for _, attrs in ancestors))
        self.assertIn("provide it to your mediator", PAGE)
        self.assertIn("Downloading is not delivery", PAGE)
        self.assertIn('id="settlement-offer-download" type="button" disabled', PAGE)
        self.assertIn('id="settlement-schedule-download" type="button" disabled', PAGE)


if __name__ == "__main__":
    unittest.main()
