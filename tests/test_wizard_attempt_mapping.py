import unittest
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

from app.wizard_attempt import plan_attempt
from app.wizard_intake import WizardIntakeDraft

CASE_ID = UUID("11111111-1111-1111-1111-111111111111")
SAVED_ON = date(2026, 11, 7)


def _draft(**overrides) -> WizardIntakeDraft:
    base = {
        "filed": "yes",
        "role": "petitioner",
        "dates": {
            "marriage": {"date": "2015-06-01"},
            "separation": {"date": "2024-02-15"},
            "cohabitation": {"date": "2013-01-10"},
            "petition": {"date": "2024-03-01"},
        },
        "finances": [
            {
                "id": "a1",
                "kind": "asset",
                "category": "Real estate",
                "description": "Family home",
                "owners": "Both",
                "holding": "joint",
                "acquisition_method": "purchase",
                "acquired_date": "2016-04-20",
                "amount": "512345.67",
            },
            {"id": "d1", "kind": "debt", "category": "Mortgage", "description": "Home loan", "amount": "301000"},
        ],
        "issues": [{"id": "i1", "topic": "Home", "outcome": "I keep the house"}],
        "agreements": [{"id": "g1", "summary": "Split the car loan", "date": "2024-05-01"}],
    }
    base.update(overrides)
    return WizardIntakeDraft.model_validate(base)


class WizardAttemptMappingTests(unittest.TestCase):
    def test_entered_amounts_become_exact_cents_for_each_asset_and_debt(self) -> None:
        plan = plan_attempt(CASE_ID, _draft(), SAVED_ON, wizard_revision=3)

        self.assertEqual(plan.needs, [])
        self.assertEqual(
            [(asset.name, asset.kind, asset.amount_cents) for asset in plan.assets],
            [("Family home", "asset", 51234567), ("Home loan", "debt", 30100000)],
        )

    def test_ids_are_stable_for_the_same_case_and_entry(self) -> None:
        first = plan_attempt(CASE_ID, _draft(), SAVED_ON, 1)
        second = plan_attempt(CASE_ID, _draft(), SAVED_ON, 2)
        other_case = plan_attempt(uuid4(), _draft(), SAVED_ON, 1)

        self.assertEqual([a.asset_id for a in first.assets], [a.asset_id for a in second.assets])
        self.assertEqual([a.event_id for a in first.assets], [a.event_id for a in second.assets])
        self.assertNotEqual(first.assets[0].asset_id, other_case.assets[0].asset_id)
        self.assertEqual(len({a.asset_id for a in first.assets}), 2)

    def test_event_date_is_the_acquired_date_else_the_save_date(self) -> None:
        plan = plan_attempt(CASE_ID, _draft(), SAVED_ON, 1)

        self.assertEqual([a.effective_date for a in plan.assets], [date(2016, 4, 20), SAVED_ON])

    def test_names_fall_back_to_category_then_a_numbered_label(self) -> None:
        draft = _draft(
            finances=[
                {"id": "a", "kind": "asset", "category": "Savings", "description": "  ", "amount": "10"},
                {"id": "b", "kind": "asset", "amount": "20"},
                {"id": "c", "kind": "debt", "amount": "30"},
            ]
        )

        plan = plan_attempt(CASE_ID, draft, SAVED_ON, 1)

        self.assertEqual([a.name for a in plan.assets], ["Savings", "Asset 2", "Debt 3"])

    def test_the_note_keeps_entered_details_without_classifying_them(self) -> None:
        plan = plan_attempt(CASE_ID, _draft(), SAVED_ON, 1)

        note = plan.assets[0].note
        for text in ("Real estate", "Both", "joint", "purchase"):
            self.assertIn(text, note)
        self.assertNotIn("community", note.casefold())
        self.assertNotIn("separate", note.casefold())

    def test_entries_without_a_positive_amount_are_reported_not_added(self) -> None:
        draft = _draft(
            finances=[
                {"id": "a", "kind": "asset", "description": "Has value", "amount": "5"},
                {"id": "b", "kind": "asset", "description": "No amount"},
                {"id": "c", "kind": "debt", "description": "Zero", "amount": "0"},
            ]
        )

        plan = plan_attempt(CASE_ID, draft, SAVED_ON, 1)

        self.assertEqual([a.name for a in plan.assets], ["Has value"])
        excluded = {item["label"]: item["reason"] for item in plan.report["excluded"]}
        self.assertEqual(excluded["No amount"], "No amount was entered.")
        self.assertEqual(excluded["Zero"], "The amount is zero.")

    def test_relationship_window_uses_the_marriage_date_when_known(self) -> None:
        plan = plan_attempt(CASE_ID, _draft(), SAVED_ON, 1)

        window = plan.axes["relationship_windows"][0]
        self.assertEqual(window["start_date"], "2015-06-01")
        self.assertEqual(window["separation_date"], "2024-02-15")
        self.assertEqual(window["relationship_type"], "marriage_only")
        self.assertEqual(window["label"], "As entered in your case information")
        self.assertEqual(plan.axes["tracing_methods"], ["explicit"])
        self.assertEqual(plan.axes["community_share_bps"], [5000])

    def test_cohabitation_start_is_an_alternate_window_with_a_non_legal_note(self) -> None:
        draft = _draft(
            dates={
                "marriage": {"unknown": True},
                "cohabitation": {"date": "2013-01-10"},
                "separation": {"date": "2024-02-15"},
            }
        )

        window = plan_attempt(CASE_ID, draft, SAVED_ON, 1).axes["relationship_windows"][0]

        self.assertEqual(window["start_date"], "2013-01-10")
        self.assertEqual(window["relationship_type"], "alternate")
        self.assertIn("not a legal classification", window["assumption_note"])

    def test_missing_inputs_are_named_and_nothing_is_planned(self) -> None:
        draft = _draft(
            dates={"marriage": {"unknown": True}, "separation": {"unknown": True}},
            finances=[{"id": "x", "kind": "asset", "description": "No value"}],
        )

        plan = plan_attempt(CASE_ID, draft, SAVED_ON, 1)

        self.assertEqual(
            plan.needs,
            [
                "At least one asset or debt with an amount greater than zero.",
                "A marriage or cohabitation start date.",
                "A separation date.",
            ],
        )
        self.assertIsNone(plan.axes)

    def test_a_start_date_after_separation_is_reported(self) -> None:
        draft = _draft(dates={"marriage": {"date": "2025-01-01"}, "separation": {"date": "2024-01-01"}})

        self.assertEqual(
            plan_attempt(CASE_ID, draft, SAVED_ON, 1).needs,
            ["The start date must not be after the separation date."],
        )

    def test_role_dates_issues_and_agreements_flow_through_as_entered(self) -> None:
        plan = plan_attempt(CASE_ID, _draft(), SAVED_ON, 1)

        self.assertEqual((plan.offer_from, plan.offer_to), ("Petitioner", "Respondent"))
        self.assertEqual(
            plan.milestones,
            [
                {"name": "Cohabitation start", "date": "2013-01-10"},
                {"name": "Marriage", "date": "2015-06-01"},
                {"name": "Separation", "date": "2024-02-15"},
                {"name": "Petition filed", "date": "2024-03-01"},
            ],
        )
        self.assertEqual(
            plan.proposal_terms,
            ["Issue — Home: I keep the house", "Agreement — Split the car loan (2024-05-01)"],
        )

    def test_respondent_role_reverses_the_parties(self) -> None:
        plan = plan_attempt(CASE_ID, _draft(role="respondent"), SAVED_ON, 1)

        self.assertEqual((plan.offer_from, plan.offer_to), ("Respondent", "Petitioner"))

    def test_no_role_leaves_the_parties_empty(self) -> None:
        plan = plan_attempt(CASE_ID, _draft(role=None), SAVED_ON, 1)

        self.assertEqual((plan.offer_from, plan.offer_to), ("", ""))

    def test_terms_over_the_limits_are_reported_not_silently_cut(self) -> None:
        issues = [{"id": f"i{n}", "topic": "T", "outcome": "O"} for n in range(81)]
        issues.append({"id": "long", "topic": "L" * 240, "outcome": "x" * 2000})
        plan = plan_attempt(CASE_ID, _draft(issues=issues, agreements=[]), SAVED_ON, 1)

        self.assertEqual(len(plan.proposal_terms), 80)
        reasons = {item["reason"] for item in plan.report["excluded"] if item["kind"] == "issue"}
        self.assertIn("The proposal supports at most 80 terms.", reasons)
        self.assertIn("Too long for a proposal term (2,000 characters).", reasons)

    def test_the_report_lists_only_what_was_entered(self) -> None:
        plan = plan_attempt(CASE_ID, _draft(), SAVED_ON, wizard_revision=7)

        report = plan.report
        self.assertEqual(report["wizard_revision"], 7)
        self.assertEqual(
            [(item["label"], item["kind"], item["amount_cents"]) for item in report["included"]],
            [("Family home", "asset", 51234567), ("Home loan", "debt", 30100000)],
        )
        self.assertEqual(report["dates"], {"start": "2015-06-01", "start_source": "marriage", "separation": "2024-02-15"})
        self.assertEqual(report["role"], "petitioner")
        self.assertEqual(report["milestones"], 4)
        self.assertEqual(report["terms"], 2)
        self.assertNotIn("sample", str(report).casefold())

    def test_amounts_never_pick_up_float_rounding(self) -> None:
        draft = _draft(finances=[{"id": "a", "kind": "asset", "description": "x", "amount": "0.29"}])

        self.assertEqual(plan_attempt(CASE_ID, draft, SAVED_ON, 1).assets[0].amount_cents, 29)
        self.assertEqual(Decimal("0.29") * 100, Decimal("29.00"))


if __name__ == "__main__":
    unittest.main()
