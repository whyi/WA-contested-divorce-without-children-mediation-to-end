import unittest

from app.models import (
    AuthAuditEvent,
    AuthChallenge,
    AuthRateLimit,
    AuthSession,
    AuthToken,
    Case,
    CaseProfileAdoption,
    CaseProfileFact,
    CaseProfileFactEvent,
    CaseMembership,
    DocumentAnalysisConsent,
    DocumentAnalysisJob,
    DocumentAnalysisProposal,
    DocumentAnalysisRequest,
    ProposalReviewEvent,
    ExternalIdentity,
    MaterialImportBatch,
    MaterialImportItem,
    PasskeyCredential,
    RecoveryCode,
    RefreshToken,
    TotpCredential,
    User,
)


class AuthenticationModelTests(unittest.TestCase):
    def test_authentication_tables_are_registered(self) -> None:
        expected = {
            "users",
            "external_identities",
            "auth_sessions",
            "refresh_tokens",
            "auth_tokens",
            "totp_credentials",
            "passkey_credentials",
            "auth_challenges",
            "recovery_codes",
            "auth_rate_limits",
            "auth_audit_events",
            "case_memberships",
            "cases",
            "material_import_batches",
            "material_import_items",
            "document_analysis_consents",
            "document_analysis_requests",
            "document_analysis_jobs",
            "document_analysis_proposals",
            "analysis_proposal_review_events",
            "case_profile_adoptions",
            "case_profile_facts",
            "case_profile_fact_events",
        }
        actual = {
            model.__tablename__
            for model in (
                User,
                ExternalIdentity,
                AuthSession,
                RefreshToken,
                AuthToken,
                TotpCredential,
                PasskeyCredential,
                AuthChallenge,
                RecoveryCode,
                AuthAuditEvent,
                AuthRateLimit,
                CaseMembership,
                Case,
                MaterialImportBatch,
                MaterialImportItem,
                DocumentAnalysisConsent,
                DocumentAnalysisRequest,
                DocumentAnalysisJob,
                DocumentAnalysisProposal,
                ProposalReviewEvent,
                CaseProfileAdoption,
                CaseProfileFact,
                CaseProfileFactEvent,
            )
        }

        self.assertEqual(actual, expected)

    def test_analysis_jobs_and_proposals_keep_source_provenance(self) -> None:
        self.assertIn("source_sha256", DocumentAnalysisJob.__table__.c)
        self.assertIn("source_quote", DocumentAnalysisProposal.__table__.c)
        self.assertIn("source_page_number", DocumentAnalysisProposal.__table__.c)
        self.assertIn(
            "ck_document_analysis_jobs_status",
            {constraint.name for constraint in DocumentAnalysisJob.__table__.constraints},
        )
        self.assertIn(
            "uq_document_analysis_job_request_document",
            {constraint.name for constraint in DocumentAnalysisJob.__table__.constraints},
        )

    def test_provider_and_case_access_constraints_are_explicit(self) -> None:
        self.assertIn(
            "uq_external_identity_provider_subject",
            {constraint.name for constraint in ExternalIdentity.__table__.constraints},
        )
        self.assertIn(
            "uq_case_membership_user_case",
            {constraint.name for constraint in CaseMembership.__table__.constraints},
        )
        self.assertIn("public_key", PasskeyCredential.__table__.columns)
        self.assertNotIn("private_key", PasskeyCredential.__table__.columns)

    def test_case_profile_facts_are_append_only_and_keep_source_provenance(self) -> None:
        self.assertIn("profile_revision", Case.__table__.c)
        self.assertIn("proposal_id_snapshot", CaseProfileFact.__table__.c)
        self.assertIn("source_document_id", CaseProfileFact.__table__.c)
        self.assertIn("source_sha256", CaseProfileFact.__table__.c)
        self.assertIn("source_quote", CaseProfileFact.__table__.c)
        self.assertIn("review_decision", CaseProfileFact.__table__.c)
        self.assertIn("idempotency_key", ProposalReviewEvent.__table__.c)
        self.assertIn("action", CaseProfileFactEvent.__table__.c)
        self.assertIn("profile_revision_after", CaseProfileAdoption.__table__.c)


if __name__ == "__main__":
    unittest.main()
