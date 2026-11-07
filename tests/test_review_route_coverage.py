import unittest
from datetime import UTC, datetime
from types import SimpleNamespace
from unittest.mock import Mock, patch
from uuid import uuid4

from fastapi import HTTPException, Response
from sqlalchemy.exc import SQLAlchemyError

from app.review import (
    AdoptionCreate,
    FactDispositionCreate,
    ProposalReviewCreate,
    _active_fact_dispositions,
    _profile_fact_read,
    _quote_matches,
    _request_sha256,
    adopt_case_profile_facts,
    case_profile_facts,
    get_case_document_source_text,
    get_case_profile_facts,
    get_case_proposal_review,
    proposal_review_list,
    record_proposal_review,
    review_case_proposal,
    source_text,
    withdraw_case_profile_fact,
)


class ProposalReviewCoverageTests(unittest.TestCase):
    def test_quote_matching_requires_one_page_with_exact_page_number_and_quote(self) -> None:
        pages = [
            {"page_number": 1, "text": "Income: $5,000"},
            {"page_number": 2, "text": "Income: $5,000"},
        ]
        self.assertTrue(_quote_matches(pages, "Income: $5,000", 1))
        self.assertFalse(_quote_matches(pages, "Income: $5,000", 3))
        self.assertFalse(_quote_matches(pages, "Income: $6,000", 1))
        self.assertFalse(_quote_matches(pages, "", 1))
        self.assertFalse(_quote_matches({"page_number": 1}, "Income", 1))
        self.assertFalse(
            _quote_matches(
                [
                    {"page_number": 1, "text": "first copy"},
                    {"page_number": 1, "text": "second copy"},
                ],
                "copy",
                1,
            )
        )

    def test_profile_fact_read_marks_source_unavailable_and_serializes_history(self) -> None:
        fact = SimpleNamespace(
            id=uuid4(),
            case_id=uuid4(),
            proposal_id_snapshot=uuid4(),
            field_key="monthly_income",
            value="$5,000",
            original_value="$4,800",
            source_document_id=uuid4(),
            source_sha256="a" * 64,
            source_quote="Income: $4,800",
            source_page_number=1,
            provider="provider",
            model_id="model",
            notice_version="notice-1",
            review_decision="edited",
            adopted_by_snapshot=uuid4(),
            adopted_at=datetime.now(UTC),
            profile_revision=2,
        )
        history_event = SimpleNamespace(
            id=uuid4(),
            action="withdrawn",
            replacement_fact_id=None,
            profile_revision=3,
            created_at=datetime.now(UTC),
        )
        db = Mock()
        db.get.return_value = None

        result = _profile_fact_read(db, fact, history_event, True, [history_event])

        self.assertEqual(result.disposition, "withdrawn")
        self.assertTrue(result.conflict)
        self.assertFalse(result.source_available)
        self.assertEqual(result.history[0].action, "withdrawn")

    def test_reinstated_fact_is_active_and_empty_disposition_lookup_skips_database(self) -> None:
        db = Mock()
        self.assertEqual(_active_fact_dispositions(db, uuid4(), []), {})
        db.scalars.assert_not_called()

        fact = SimpleNamespace(
            id=uuid4(),
            case_id=uuid4(),
            proposal_id_snapshot=uuid4(),
            field_key="asset",
            value="house",
            original_value="house",
            source_document_id=uuid4(),
            source_sha256="b" * 64,
            source_quote="house",
            source_page_number=None,
            provider="provider",
            model_id="model",
            notice_version="notice-1",
            review_decision="accepted",
            adopted_by_snapshot=uuid4(),
            adopted_at=datetime.now(UTC),
            profile_revision=1,
        )
        db.get.return_value = SimpleNamespace(
            case_id=fact.case_id,
            sha256=fact.source_sha256,
        )
        event = SimpleNamespace(
            id=uuid4(),
            action="reinstated",
            replacement_fact_id=None,
            profile_revision=2,
            created_at=datetime.now(UTC),
        )
        result = _profile_fact_read(db, fact, event, False, [event])
        self.assertEqual(result.disposition, "active")
        self.assertTrue(result.source_available)
        self.assertFalse(result.conflict)

    def test_review_list_requires_an_analysis_request(self) -> None:
        db = Mock()
        db.scalar.return_value = None
        with self.assertRaises(HTTPException) as raised:
            proposal_review_list(db, uuid4(), uuid4())
        self.assertEqual(raised.exception.status_code, 404)

    def test_review_list_includes_evidence_status_urls_and_review_history(self) -> None:
        case_id, request_id = uuid4(), uuid4()
        pdf_id, docx_id = uuid4(), uuid4()
        pdf_proposal = SimpleNamespace(
            id=uuid4(),
            document_id=pdf_id,
            field_key="monthly_income",
            value="$5,000",
            source_sha256="c" * 64,
            source_quote="Income: $5,000",
            source_page_number=2,
            confidence="high",
            uncertainty="",
        )
        docx_proposal = SimpleNamespace(
            id=uuid4(),
            document_id=docx_id,
            field_key="monthly_expense",
            value="$2,000",
            source_sha256="d" * 64,
            source_quote="Expenses: $2,000",
            source_page_number=None,
            confidence="medium",
            uncertainty="Check source",
        )
        accepted = SimpleNamespace(
            id=uuid4(),
            decision="accepted",
            edited_value=None,
            created_at=datetime.now(UTC),
        )
        edited = SimpleNamespace(
            id=uuid4(),
            decision="edited",
            edited_value="$2,100",
            created_at=datetime.now(UTC),
        )
        pdf_document = SimpleNamespace(extension="pdf")
        pdf_extraction = SimpleNamespace(pages_json=[])
        db = Mock()
        db.scalar.return_value = SimpleNamespace(id=request_id)
        db.scalars.side_effect = [
            Mock(**{"all.return_value": [pdf_proposal, docx_proposal]}),
            Mock(**{"all.return_value": [accepted]}),
            Mock(**{"all.return_value": [accepted, edited]}),
        ]
        with patch(
            "app.review._proposal_evidence",
            side_effect=[(pdf_document, pdf_extraction), None],
        ):
            result = proposal_review_list(db, case_id, request_id)

        pdf_result, docx_result = result.proposals
        self.assertEqual(result.request_id, request_id)
        self.assertEqual(pdf_result.evidence_status, "available")
        self.assertEqual(
            pdf_result.source_file_url,
            f"/documents/{pdf_id}/preview#page=2",
        )
        self.assertEqual(pdf_result.review_decision, "accepted")
        self.assertEqual(pdf_result.reviewed_value, "$5,000")
        self.assertEqual(len(pdf_result.review_history), 1)
        self.assertEqual(docx_result.evidence_status, "unavailable")
        self.assertIsNone(docx_result.source_file_url)
        self.assertEqual(docx_result.source_text_url, f"/cases/{case_id}/documents/{docx_id}/source-text")
        self.assertEqual(docx_result.review_decision, "edited")
        self.assertEqual(docx_result.reviewed_value, "$2,100")

    def test_review_list_returns_none_for_unreviewed_proposal_and_non_pdf_source(self) -> None:
        case_id, request_id, document_id = uuid4(), uuid4(), uuid4()
        proposal = SimpleNamespace(
            id=uuid4(),
            document_id=document_id,
            field_key="asset",
            value="house",
            source_sha256="e" * 64,
            source_quote="house",
            source_page_number=None,
            confidence="low",
            uncertainty="Uncertain",
        )
        db = Mock()
        db.scalar.return_value = SimpleNamespace(id=request_id)
        db.scalars.side_effect = [
            Mock(**{"all.return_value": [proposal]}),
            Mock(**{"all.return_value": []}),
        ]
        with patch(
            "app.review._proposal_evidence",
            return_value=(SimpleNamespace(extension="docx"), SimpleNamespace()),
        ):
            result = proposal_review_list(db, case_id, request_id)
        self.assertEqual(result.proposals[0].evidence_status, "available")
        self.assertIsNone(result.proposals[0].source_file_url)
        self.assertIsNone(result.proposals[0].review_decision)
        self.assertIsNone(result.proposals[0].reviewed_value)

    def test_source_text_reports_missing_document_extraction_and_malformed_pages(self) -> None:
        case_id, document_id = uuid4(), uuid4()
        db = Mock()
        db.get.return_value = None
        with self.assertRaises(HTTPException) as raised:
            source_text(db, case_id, document_id)
        self.assertEqual(raised.exception.status_code, 404)

        db.get.return_value = SimpleNamespace(case_id=case_id)
        db.scalar.return_value = SimpleNamespace(pages_json=None)
        with self.assertRaises(HTTPException) as raised:
            source_text(db, case_id, document_id)
        self.assertEqual(raised.exception.status_code, 404)

        for invalid_page in (
            "not a page",
            {"page_number": 0, "text": "bad page"},
            {"page_number": True, "text": "bool is not a page number"},
            {"page_number": 1, "text": None},
        ):
            with self.subTest(invalid_page=invalid_page):
                db.scalar.return_value = SimpleNamespace(pages_json=[invalid_page])
                with self.assertRaises(HTTPException) as raised:
                    source_text(db, case_id, document_id)
                self.assertEqual(raised.exception.status_code, 503)

    def test_source_text_hides_documents_from_other_cases(self) -> None:
        db = Mock()
        db.get.return_value = SimpleNamespace(case_id=uuid4())
        with self.assertRaises(HTTPException) as raised:
            source_text(db, uuid4(), uuid4())
        self.assertEqual(raised.exception.status_code, 404)
        db.scalar.assert_not_called()

    def test_review_idempotency_rejects_reuse_with_a_different_payload(self) -> None:
        case_id, user_id, key = uuid4(), uuid4(), uuid4()
        existing = SimpleNamespace(
            request_sha256=_request_sha256(
                {
                    "proposal_id": str(uuid4()),
                    "decision": "accepted",
                    "edited_value": None,
                }
            )
        )
        db = Mock()
        db.scalar.return_value = existing

        with self.assertRaises(HTTPException) as raised:
            record_proposal_review(
                db,
                case_id,
                uuid4(),
                uuid4(),
                user_id,
                ProposalReviewCreate(idempotency_key=key, decision="rejected"),
            )
        self.assertEqual(raised.exception.status_code, 409)
        db.commit.assert_not_called()

    def test_case_profile_lookup_hides_unknown_case(self) -> None:
        db = Mock()
        db.get.return_value = None
        with self.assertRaises(HTTPException) as raised:
            case_profile_facts(db, uuid4())
        self.assertEqual(raised.exception.status_code, 404)
        db.scalars.assert_not_called()


class ProposalReviewRouteCoverageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.case_id = uuid4()
        self.request_id = uuid4()
        self.user = SimpleNamespace(id=uuid4())
        self.db = Mock()
        self.response = Response()

    def test_read_routes_authorize_read_access_set_no_store_and_return_service_result(self) -> None:
        expected = object()
        routes = (
            (
                get_case_proposal_review,
                (self.case_id, self.request_id, self.response, self.user, self.db),
                "proposal_review_list",
            ),
            (
                get_case_profile_facts,
                (self.case_id, self.response, self.user, self.db),
                "case_profile_facts",
            ),
            (
                get_case_document_source_text,
                (self.case_id, uuid4(), self.response, self.user, self.db),
                "source_text",
            ),
        )
        for route, args, service in routes:
            with self.subTest(route=route.__name__):
                response = Response()
                with (
                    patch("app.review._authorize_case") as authorize,
                    patch(f"app.review.{service}", return_value=expected) as call,
                ):
                    if route is get_case_proposal_review:
                        result = route(self.case_id, self.request_id, response, self.user, self.db)
                    elif route is get_case_profile_facts:
                        result = route(self.case_id, response, self.user, self.db)
                    else:
                        result = route(self.case_id, args[1], response, self.user, self.db)
                self.assertIs(result, expected)
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                authorize.assert_called_once_with(self.db, self.user, self.case_id, write=False)
                call.assert_called_once()

    def test_write_routes_authorize_write_access_and_set_no_store(self) -> None:
        payloads = (
            (
                review_case_proposal,
                (
                    self.case_id,
                    self.request_id,
                    uuid4(),
                    ProposalReviewCreate(idempotency_key=uuid4(), decision="accepted"),
                ),
                "record_proposal_review",
            ),
            (
                adopt_case_profile_facts,
                (
                    self.case_id,
                    AdoptionCreate(
                        idempotency_key=uuid4(),
                        expected_profile_revision=0,
                        proposal_ids=[uuid4()],
                        confirm=True,
                    ),
                ),
                "adopt_case_proposals",
            ),
            (
                withdraw_case_profile_fact,
                (
                    self.case_id,
                    uuid4(),
                    FactDispositionCreate(
                        idempotency_key=uuid4(),
                        expected_profile_revision=0,
                        action="withdrawn",
                        confirm=True,
                    ),
                ),
                "withdraw_case_fact",
            ),
        )
        for route, route_args, service in payloads:
            with self.subTest(route=route.__name__):
                response = Response()
                event = SimpleNamespace(
                    id=uuid4(),
                    decision="accepted",
                    edited_value=None,
                    created_at=datetime.now(UTC),
                )
                with (
                    patch("app.review._authorize_case") as authorize,
                    patch(f"app.review.{service}", return_value=event) as call,
                ):
                    if route is review_case_proposal:
                        result = route(
                            route_args[0],
                            route_args[1],
                            route_args[2],
                            route_args[3],
                            response,
                            self.user,
                            self.db,
                        )
                    elif route is adopt_case_profile_facts:
                        result = route(
                            route_args[0],
                            route_args[1],
                            response,
                            self.user,
                            self.db,
                        )
                    else:
                        result = route(
                            route_args[0],
                            route_args[1],
                            route_args[2],
                            response,
                            self.user,
                            self.db,
                        )
                self.assertEqual(response.headers["Cache-Control"], "no-store")
                authorize.assert_called_once_with(self.db, self.user, self.case_id, write=True)
                call.assert_called_once()
                self.assertIsNotNone(result)

    def test_sqlalchemy_errors_are_logged_mapped_and_rolled_back_on_writes(self) -> None:
        route_calls = (
            (
                get_case_proposal_review,
                (self.case_id, self.request_id, self.user, self.db),
                "proposal_review_list",
                "Proposal review is unavailable.",
                False,
            ),
            (
                review_case_proposal,
                (
                    self.case_id,
                    self.request_id,
                    uuid4(),
                    ProposalReviewCreate(idempotency_key=uuid4(), decision="accepted"),
                    self.user,
                    self.db,
                ),
                "record_proposal_review",
                "Proposal review could not be saved.",
                True,
            ),
            (
                adopt_case_profile_facts,
                (
                    self.case_id,
                    AdoptionCreate(
                        idempotency_key=uuid4(),
                        expected_profile_revision=0,
                        proposal_ids=[uuid4()],
                        confirm=True,
                    ),
                    self.user,
                    self.db,
                ),
                "adopt_case_proposals",
                "Selected suggestions could not be adopted.",
                True,
            ),
            (
                get_case_profile_facts,
                (self.case_id, self.user, self.db),
                "case_profile_facts",
                "Case-profile facts are unavailable.",
                False,
            ),
            (
                withdraw_case_profile_fact,
                (
                    self.case_id,
                    uuid4(),
                    FactDispositionCreate(
                        idempotency_key=uuid4(),
                        expected_profile_revision=0,
                        action="withdrawn",
                        confirm=True,
                    ),
                    self.user,
                    self.db,
                ),
                "withdraw_case_fact",
                "Case-profile fact could not be withdrawn.",
                True,
            ),
            (
                get_case_document_source_text,
                (self.case_id, uuid4(), self.user, self.db),
                "source_text",
                "Source text is unavailable.",
                False,
            ),
        )
        for route, business_args, service, detail, is_write in route_calls:
            with self.subTest(route=route.__name__):
                response = Response()
                if route in (get_case_proposal_review, review_case_proposal):
                    route_args = (*business_args[:-2], response, *business_args[-2:])
                elif route in (adopt_case_profile_facts, withdraw_case_profile_fact):
                    if route is adopt_case_profile_facts:
                        route_args = (business_args[0], business_args[1], response, *business_args[2:])
                    else:
                        route_args = (
                            business_args[0],
                            business_args[1],
                            business_args[2],
                            response,
                            *business_args[3:],
                        )
                elif route is get_case_profile_facts:
                    route_args = (business_args[0], response, *business_args[1:])
                else:
                    route_args = (business_args[0], business_args[1], response, *business_args[2:])
                with (
                    patch("app.review._authorize_case"),
                    patch(f"app.review.{service}", side_effect=SQLAlchemyError("database unavailable")),
                    patch("app.review.log_failure_event") as log_failure,
                    self.assertRaises(HTTPException) as raised,
                ):
                    route(*route_args)
                self.assertEqual(raised.exception.status_code, 503)
                self.assertEqual(raised.exception.detail, detail)
                log_failure.assert_called_once()
                if is_write:
                    self.db.rollback.assert_called()

    def test_authorization_http_errors_are_not_translated_to_service_unavailable(self) -> None:
        denial = HTTPException(status_code=404, detail="Case not found.")
        with (
            patch("app.review._authorize_case", side_effect=denial),
            patch("app.review.log_failure_event") as log_failure,
            self.assertRaises(HTTPException) as raised,
        ):
            get_case_profile_facts(self.case_id, self.response, self.user, self.db)
        self.assertIs(raised.exception, denial)
        log_failure.assert_not_called()


if __name__ == "__main__":
    unittest.main()
