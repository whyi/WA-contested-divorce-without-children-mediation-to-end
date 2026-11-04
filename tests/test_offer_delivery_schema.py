import unittest
from uuid import uuid4

from pydantic import ValidationError

from app.offer_documents import MediationOfferTerms
from app.settlement_routes import OfferDelivery


class OfferDeliverySchemaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.terms = MediationOfferTerms(
            offer_from="Party A",
            offer_to="Party B",
            terms=["Each party retains the property listed in their column."],
        )

    def test_delivery_requires_explicit_confirmation(self) -> None:
        with self.assertRaises(ValidationError):
            OfferDelivery(
                channel="email",
                confirm=False,
                idempotency_key=uuid4(),
                recipient="recipient@example.com",
                terms=self.terms,
            )

    def test_email_requires_recipient_and_cloud_destinations_reject_it(self) -> None:
        with self.assertRaises(ValidationError):
            OfferDelivery(
                channel="email",
                confirm=True,
                idempotency_key=uuid4(),
                terms=self.terms,
            )
        with self.assertRaises(ValidationError):
            OfferDelivery(
                channel="google_drive",
                confirm=True,
                idempotency_key=uuid4(),
                recipient="recipient@example.com",
                terms=self.terms,
            )


if __name__ == "__main__":
    unittest.main()
