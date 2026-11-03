import unittest
from datetime import date

from pydantic import ValidationError

from app.property_tracing import (
    PropertyAsset,
    PropertyTracingUpdate,
    RelationshipMilestones,
    classify_asset,
)


class PropertyTracingTests(unittest.TestCase):
    def test_asset_acquired_before_relationship_window_is_separate_candidate(self) -> None:
        asset = PropertyAsset(
            name="Home",
            acquisition_date="2018-06-01",
            acquisition_method="purchase",
            title_status="individual",
        )
        milestones = RelationshipMilestones(
            cohabitation_start_date="2020-01-01",
            marriage_date="2021-01-01",
            separation_start_date="2025-01-01",
        )

        self.assertEqual(classify_asset(asset, milestones), "separate_property_candidate")

    def test_joint_purchase_in_relationship_window_is_community_candidate(self) -> None:
        asset = PropertyAsset(
            name="Savings",
            acquisition_date="2022-03-15",
            acquisition_method="purchase",
            title_status="joint",
        )
        milestones = RelationshipMilestones(
            cohabitation_start_date="2020-01-01",
            marriage_date="2021-01-01",
            separation_start_date="2025-01-01",
        )

        self.assertEqual(classify_asset(asset, milestones), "community_property_candidate")

    def test_inheritance_remains_separate_candidate_during_relationship(self) -> None:
        asset = PropertyAsset(
            name="Inheritance",
            acquisition_date="2022-03-15",
            acquisition_method="inheritance",
            title_status="individual",
        )
        milestones = RelationshipMilestones(
            cohabitation_start_date="2020-01-01",
            marriage_date="2021-01-01",
            separation_start_date="2025-01-01",
        )

        self.assertEqual(classify_asset(asset, milestones), "separate_property_candidate")

    def test_individually_titled_asset_during_relationship_needs_review(self) -> None:
        asset = PropertyAsset(
            name="Vehicle",
            acquisition_date="2022-03-15",
            acquisition_method="purchase",
            title_status="individual",
        )
        milestones = RelationshipMilestones(
            marriage_date="2021-01-01",
            separation_start_date="2025-01-01",
        )

        self.assertEqual(classify_asset(asset, milestones), "needs_review")

    def test_other_acquisition_method_during_relationship_needs_review(self) -> None:
        asset = PropertyAsset(
            name="Other acquisition",
            acquisition_date="2022-03-15",
            acquisition_method="other",
            title_status="joint",
        )
        milestones = RelationshipMilestones(
            marriage_date="2021-01-01",
            separation_start_date="2025-01-01",
        )

        self.assertEqual(classify_asset(asset, milestones), "needs_review")

    def test_asset_after_separation_is_post_separation_candidate(self) -> None:
        asset = PropertyAsset(
            name="New account",
            acquisition_date="2025-02-01",
            acquisition_method="purchase",
            title_status="individual",
        )
        milestones = RelationshipMilestones(separation_start_date="2025-01-01")

        self.assertEqual(classify_asset(asset, milestones), "post_separation_candidate")

    def test_missing_window_dates_require_review(self) -> None:
        asset = PropertyAsset(
            name="Unknown",
            acquisition_date="2022-03-15",
            acquisition_method="purchase",
            title_status="joint",
        )

        self.assertEqual(
            classify_asset(asset, RelationshipMilestones()),
            "needs_review",
        )

    def test_invalid_calendar_date_and_title_status_are_rejected(self) -> None:
        with self.assertRaises(ValidationError):
            PropertyAsset(
                name="Home",
                acquisition_date="2023-02-29",
                acquisition_method="purchase",
                title_status="joint",
            )
        with self.assertRaises(ValidationError):
            PropertyAsset(
                name="Home",
                acquisition_date=date(2023, 2, 28),
                acquisition_method="purchase",
                title_status="unclear",
            )

    def test_milestones_reject_non_calendar_date_inputs(self) -> None:
        with self.assertRaises(ValidationError):
            RelationshipMilestones(marriage_date="2024-01-01T00:00:00")
        with self.assertRaises(ValidationError):
            RelationshipMilestones(marriage_date="2024-02-30")
        self.assertIsNone(RelationshipMilestones(marriage_date="").marriage_date)

    def test_property_tracing_payload_requires_named_assets(self) -> None:
        with self.assertRaises(ValidationError):
            PropertyTracingUpdate(
                relationship_milestones={},
                assets=[
                    {
                        "name": "  ",
                        "acquisition_date": "2022-03-15",
                        "acquisition_method": "purchase",
                        "title_status": "joint",
                    }
                ]
            )


if __name__ == "__main__":
    unittest.main()
