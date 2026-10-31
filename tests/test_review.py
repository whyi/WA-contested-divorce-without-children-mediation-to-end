import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from uuid import uuid4
from unittest.mock import Mock

from fastapi import HTTPException
from pydantic import ValidationError

from app.models import CaseProfileFact
from app.review import (
    AdoptionCreate,
    FactDispositionCreate,
    ProposalReviewCreate,
    _authorize_case,
    _request_sha256,
    adopt_case_proposals,
    case_profile_facts,
    record_proposal_review,
    source_text,
    withdraw_case_fact,
)


class ProposalReviewContractTests(unittest.TestCase):
    def test_edit_decision_requires_a_nonempty_bounded_value(self) -> None:
        with self.assertRaises(ValidationError):
            ProposalReviewCreate(
                idempotency_key=uuid4(),
                decision="edited",
            )

        with self.assertRaises(ValidationError):
            ProposalReviewCreate(
                idempotency_key=uuid4(),
                decision="edited",
                edited_value="",
            )

        decision = ProposalReviewCreate(
            idempotency_key=uuid4(),
            decision="edited",
            edited_value="Verified value",
        )
        self.assertEqual(decision.edited_value, "Verified value")

    def test_non_edit_decisions_cannot_supply_a_replacement_value(self) -> None:
        for action in ("accepted", "rejected"):
            with self.subTest(action=action), self.assertRaises(ValidationError):
                ProposalReviewCreate(
                    idempotency_key=uuid4(),
                    decision=action,
                    edited_value="Unexpected value",
                )

    def test_adoption_requires_explicit_confirmation_and_unique_proposals(self) -> None:
        proposal_id = uuid4()
        with self.assertRaises(ValidationError):
            AdoptionCreate(
                idempotency_key=uuid4(),
                expected_profile_revision=0,
                proposal_ids=[proposal_id],
                confirm=False,
            )

        with self.assertRaises(ValidationError):
            AdoptionCreate(
                idempotency_key=uuid4(),
                expected_profile_revision=0,
                proposal_ids=[proposal_id, proposal_id],
                confirm=True,
            )

        adoption = AdoptionCreate(
            idempotency_key=uuid4(),
            expected_profile_revision=0,
            proposal_ids=[proposal_id],
            confirm=True,
        )
        self.assertEqual(adoption.proposal_ids, [proposal_id])

    def test_fact_disposition_requires_confirmation_and_profile_revision(self) -> None:
        with self.assertRaises(ValidationError):
            FactDispositionCreate(
                idempotency_key=uuid4(),
                expected_profile_revision=0,
                action="withdrawn",
                confirm=False,
            )

        disposition = FactDispositionCreate(
            idempotency_key=uuid4(),
            expected_profile_revision=0,
            action="withdrawn",
            confirm=True,
        )
        self.assertEqual(disposition.action, "withdrawn")

    def test_review_decision_is_append_only_and_does_not_adopt_a_fact(self) -> None:
        case_id = uuid4()
        request_id = uuid4()
        proposal_id = uuid4()
        document_id = uuid4()
        user_id = uuid4()
        proposal = SimpleNamespace(
            id=proposal_id,
            request_id=request_id,
            document_id=document_id,
            source_sha256="a" * 64,
            source_page_number=1,
            source_quote="Monthly income: $5,000",
            value="$5,000",
            field_key="monthly_income",
        )
        document = SimpleNamespace(
            id=document_id,
            case_id=case_id,
            sha256=proposal.source_sha256,
        )
        extraction = SimpleNamespace(
            pages_json=[{"page_number": 1, "text": "Monthly income: $5,000"}]
        )
        db = Mock()
        db.scalar.side_effect = [None, proposal, extraction]
        db.get.return_value = document
        payload = ProposalReviewCreate(
            idempotency_key=uuid4(),
            decision="edited",
            edited_value="$5,200",
        )

        result = record_proposal_review(
            db,
            case_id,
            request_id,
            proposal_id,
            user_id,
            payload,
        )

        self.assertEqual(result.decision, "edited")
        self.assertEqual(result.edited_value, "$5,200")
        review_event = db.add.call_args.args[0]
        self.assertEqual(review_event.proposal_id_snapshot, proposal_id)
        self.assertEqual(review_event.edited_value, "$5,200")
        self.assertFalse(
            any(isinstance(call.args[0], CaseProfileFact) for call in db.add.call_args_list)
        )
        db.commit.assert_called_once()

    def test_review_cannot_accept_a_missing_or_changed_source(self) -> None:
        case_id = uuid4()
        request_id = uuid4()
        proposal_id = uuid4()
        proposal = SimpleNamespace(
            id=proposal_id,
            document_id=uuid4(),
            source_sha256="c" * 64,
            source_page_number=1,
            source_quote="A source quote",
        )
        db = Mock()
        db.scalar.side_effect = [None, proposal]
        db.get.return_value = None

        with self.assertRaises(HTTPException) as raised:
            record_proposal_review(
                db,
                case_id,
                request_id,
                proposal_id,
                uuid4(),
                ProposalReviewCreate(
                    idempotency_key=uuid4(),
                    decision="accepted",
                ),
            )

        self.assertEqual(raised.exception.status_code, 409)
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_docx_source_text_reports_unavailable_physical_page(self) -> None:
        case_id = uuid4()
        document_id = uuid4()
        document = SimpleNamespace(
            id=document_id,
            case_id=case_id,
            extension="docx",
            sha256="d" * 64,
        )
        extraction = SimpleNamespace(
            pages_json=[{"page_number": None, "text": "A verified document quote."}]
        )
        db = Mock()
        db.get.return_value = document
        db.scalar.return_value = extraction

        result = source_text(db, case_id, document_id)

        self.assertEqual(result.extension, "docx")
        self.assertIsNone(result.pages[0].page_number)
        self.assertEqual(result.pages[0].text, "A verified document quote.")

    def test_case_membership_blocks_viewers_and_hides_unknown_cases(self) -> None:
        user = SimpleNamespace(id=uuid4())
        case_id = uuid4()
        db = Mock()
        db.scalar.return_value = SimpleNamespace(role="viewer")

        with self.assertRaises(HTTPException) as raised:
            _authorize_case(db, user, case_id, write=True)

        self.assertEqual(raised.exception.status_code, 403)

        db.scalar.return_value = None
        with self.assertRaises(HTTPException) as raised:
            _authorize_case(db, user, case_id, write=False)

        self.assertEqual(raised.exception.status_code, 404)

    def test_adoption_retry_returns_the_existing_outcome(self) -> None:
        case_id = uuid4()
        user_id = uuid4()
        proposal_id = uuid4()
        adoption = SimpleNamespace(
            id=uuid4(),
            case_id=case_id,
            profile_revision_after=4,
            request_sha256=_request_sha256(
                {"proposal_ids": [str(proposal_id)], "supersede_fact_ids": []}
            ),
        )
        db = Mock()
        db.scalar.return_value = adoption
        db.scalars.return_value.all.return_value = []
        payload = AdoptionCreate(
            idempotency_key=uuid4(),
            expected_profile_revision=0,
            proposal_ids=[proposal_id],
            confirm=True,
        )

        result = adopt_case_proposals(db, case_id, user_id, payload)

        self.assertEqual(result.adoption_id, adoption.id)
        self.assertEqual(result.profile_revision, 4)
        self.assertEqual(result.facts, [])
        db.commit.assert_not_called()
        db.add.assert_not_called()

        mismatched_payload = AdoptionCreate(
            idempotency_key=payload.idempotency_key,
            expected_profile_revision=0,
            proposal_ids=[uuid4()],
            confirm=True,
        )
        with self.assertRaises(HTTPException) as raised:
            adopt_case_proposals(db, case_id, user_id, mismatched_payload)

        self.assertEqual(raised.exception.status_code, 409)

    def test_withdrawal_retry_returns_the_existing_event(self) -> None:
        case_id = uuid4()
        fact_id = uuid4()
        existing = SimpleNamespace(
            fact_id=fact_id,
            action="withdrawn",
            profile_revision=5,
            request_sha256=_request_sha256(
                {"fact_id": str(fact_id), "action": "withdrawn"}
            ),
        )
        db = Mock()
        db.scalar.return_value = existing
        payload = FactDispositionCreate(
            idempotency_key=uuid4(),
            expected_profile_revision=0,
            action="withdrawn",
            confirm=True,
        )

        result = withdraw_case_fact(db, case_id, fact_id, uuid4(), payload)

        self.assertEqual(result.fact_id, fact_id)
        self.assertEqual(result.profile_revision, 5)
        db.commit.assert_not_called()
        db.add.assert_not_called()

    def test_same_field_facts_are_both_preserved_and_marked_as_conflicts(self) -> None:
        case_id = uuid4()
        now = datetime.now(UTC)

        def fact(value: str) -> SimpleNamespace:
            return SimpleNamespace(
                id=uuid4(),
                case_id=case_id,
                proposal_id_snapshot=uuid4(),
                field_key="monthly_income",
                value=value,
                original_value=value,
                source_document_id=uuid4(),
                source_sha256="e" * 64,
                source_quote=f"Income: {value}",
                source_page_number=1,
                provider="Amazon Bedrock",
                model_id="test-model",
                notice_version="notice-1",
                review_decision="accepted",
                adopted_by_snapshot=uuid4(),
                adopted_at=now,
                profile_revision=1,
            )

        first, second = fact("$5,000"), fact("$5,200")
        case = SimpleNamespace(id=case_id, profile_revision=1)
        document = SimpleNamespace(case_id=case_id, sha256="e" * 64)
        db = Mock()
        db.get.side_effect = [case, document, document]
        results = [
            [first, second],
            [],
        ]
        db.scalars.side_effect = [
            SimpleNamespace(all=lambda rows=rows: rows)
            for rows in results
        ]

        result = case_profile_facts(db, case_id)

        self.assertEqual([item.value for item in result.facts], ["$5,000", "$5,200"])
        self.assertTrue(all(item.conflict for item in result.facts))
        self.assertTrue(all(item.source_available for item in result.facts))

    def test_stale_profile_revision_does_not_partially_adopt(self) -> None:
        case_id = uuid4()
        case = SimpleNamespace(
            id=case_id,
            profile_revision=3,
            metadata_json={"existing": "keep"},
            asset_liability_inventory={"house": "keep"},
        )
        db = Mock()
        db.scalar.side_effect = [None, case, None]
        payload = AdoptionCreate(
            idempotency_key=uuid4(),
            expected_profile_revision=2,
            proposal_ids=[uuid4()],
            confirm=True,
        )

        with self.assertRaises(HTTPException) as raised:
            adopt_case_proposals(db, case_id, uuid4(), payload)

        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(case.metadata_json, {"existing": "keep"})
        self.assertEqual(case.asset_liability_inventory, {"house": "keep"})
        db.add.assert_not_called()
        db.commit.assert_not_called()

    def test_adoption_uses_reviewed_value_and_keeps_json_profile_unchanged(self) -> None:
        case_id = uuid4()
        user_id = uuid4()
        proposal_id = uuid4()
        document_id = uuid4()
        case = SimpleNamespace(
            id=case_id,
            profile_revision=3,
            metadata_json={"existing": "keep"},
            asset_liability_inventory={"house": "keep"},
        )
        proposal = SimpleNamespace(
            id=proposal_id,
            job_id=uuid4(),
            document_id=document_id,
            source_sha256="b" * 64,
            field_key="monthly_income",
            value="$5,000",
            source_quote="Monthly income: $5,000",
            source_page_number=1,
        )
        review = SimpleNamespace(
            proposal_id_snapshot=proposal_id,
            decision="edited",
            edited_value="$5,200",
        )
        document = SimpleNamespace(id=document_id, case_id=case_id, sha256=proposal.source_sha256)
        extraction = SimpleNamespace(
            pages_json=[{"page_number": 1, "text": "Monthly income: $5,000"}]
        )
        consent = SimpleNamespace(
            provider="Amazon Bedrock",
            model_id="test-model",
            notice_version="notice-1",
        )
        db = Mock()
        db.scalar.side_effect = [None, case, None, extraction, consent]
        db.get.return_value = document
        scalars_results = [[proposal], [], [review]]
        scalars_call_count = 0

        def scalars_side_effect(_query):
            nonlocal scalars_call_count
            scalars_call_count += 1
            if scalars_results:
                result = scalars_results.pop(0)
            elif scalars_call_count == 4:
                result = [
                    item
                    for item in db.add_all.call_args_list[0].args[0]
                    if isinstance(item, CaseProfileFact)
                ]
            else:
                result = []
            scalar_result = Mock()
            scalar_result.all.return_value = result
            return scalar_result

        db.scalars.side_effect = scalars_side_effect
        payload = AdoptionCreate(
            idempotency_key=uuid4(),
            expected_profile_revision=3,
            proposal_ids=[proposal_id],
            confirm=True,
        )

        adopted = adopt_case_proposals(db, case_id, user_id, payload)

        self.assertEqual(adopted.profile_revision, 4)
        self.assertEqual(len(adopted.facts), 1)
        fact = adopted.facts[0]
        self.assertEqual(fact.value, "$5,200")
        self.assertEqual(fact.original_value, "$5,000")
        self.assertEqual(fact.source_quote, proposal.source_quote)
        self.assertEqual(fact.source_document_id, document_id)
        self.assertEqual(fact.model_id, "test-model")
        self.assertEqual(fact.adopted_by, user_id)
        self.assertEqual(fact.adopted_at.tzinfo, UTC)
        self.assertEqual(case.profile_revision, 4)
        self.assertEqual(case.metadata_json, {"existing": "keep"})
        self.assertEqual(case.asset_liability_inventory, {"house": "keep"})
        db.commit.assert_called_once()


if __name__ == "__main__":
    unittest.main()
