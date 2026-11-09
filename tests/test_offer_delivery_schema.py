import unittest
from pathlib import Path


class OfferDeliverySchemaTests(unittest.TestCase):
    def test_proposal_documents_are_not_sent_or_receipt_verified_by_the_app(self) -> None:
        app_dir = Path(__file__).parents[1] / "src" / "app"
        sources = "\n".join(
            path.read_text(encoding="utf-8")
            for path in app_dir.glob("*.py")
        )
        self.assertNotIn("class OfferDelivery", sources)
        self.assertNotIn("/offer-response/complete", sources)
        self.assertIn('"delivery_verified_by_app": False', sources)
        self.assertIn('"response_verified_by_app": False', sources)


if __name__ == "__main__":
    unittest.main()
