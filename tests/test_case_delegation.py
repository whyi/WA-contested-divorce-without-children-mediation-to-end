import unittest
from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch
from uuid import uuid4

from fastapi import HTTPException, Response
from sqlalchemy import create_engine, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.auth import hash_token
from app.case_delegation import (
    DelegationAccept,
    DelegationInvite,
    accept_delegation,
    get_delegation,
    invite_delegate,
    resolve_case_access,
    revoke_delegation,
)
from app.case_lifecycle import lifecycle_write_allowed
from app.case_limits import require_active_case_slot
from app.database import Base
from app.models import AuthAuditEvent, Case, CaseDelegationInvitation, CaseMembership, User


@compiles(JSONB, "sqlite")
def _jsonb_for_sqlite(_type, _compiler, **_kwargs) -> str:
    return "JSON"


class DelegationFixture(unittest.TestCase):
    def setUp(self) -> None:
        self._defaults = []
        for table in Base.metadata.tables.values():
            for column in table.columns:
                default = column.server_default
                if default is not None and "::" in str(getattr(default, "arg", "")):
                    self._defaults.append((column, default))
                    column.server_default = None
        engine = create_engine(
            "sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False}
        )
        Base.metadata.create_all(engine)
        self.db = Session(engine)
        self.party = User(email="party@example.com", status="active")
        self.other_party = User(email="other@example.com", status="active")
        self.pro = User(email="Lawyer@Example.com".casefold(), status="active", account_type="professional")
        self.stranger = User(email="stranger@example.com", status="active", account_type="professional")
        self.db.add_all([self.party, self.other_party, self.pro, self.stranger])
        self.db.flush()
        self.case = self._case(self.party)
        self.sent: list[tuple[str, str, str]] = []
        patches = [
            patch("app.case_delegation._rate_limit"),
            patch("app.case_delegation._require_email_config"),
            patch(
                "app.case_delegation._send_email",
                side_effect=lambda to, subject, body: self.sent.append((to, subject, body)),
            ),
        ]
        for item in patches:
            item.start()
            self.addCleanup(item.stop)

    def tearDown(self) -> None:
        self.db.close()
        for column, default in self._defaults:
            column.server_default = default

    def _case(self, owner: User) -> Case:
        case = Case(status="draft", metadata_json={})
        self.db.add(case)
        self.db.flush()
        self.db.add(CaseMembership(case_id=case.id, user_id=owner.id, role="owner"))
        self.db.commit()
        return case

    def request(self, user: User) -> SimpleNamespace:
        return SimpleNamespace(state=SimpleNamespace(user_id=user.id), client=None)

    def invite(self, email: str = "lawyer@example.com", case: Case | None = None, user: User | None = None):
        return invite_delegate(
            (case or self.case).id,
            DelegationInvite(email=email),
            self.request(user or self.party),
            Response(),
            self.db,
        )

    def token(self) -> str:
        return self.sent[-1][2].rsplit(": ", 1)[1].split("\n")[0]

    def accept(self, user: User, token: str | None = None):
        return accept_delegation(
            DelegationAccept(token=token or self.token()),
            self.request(user),
            Response(),
            user,
            self.db,
        )

    def revoke(self, user: User | None = None, case: Case | None = None):
        return revoke_delegation(
            (case or self.case).id, self.request(user or self.party), Response(), self.db
        )

    def access(self, user: User, case: Case | None = None, path: str | None = None):
        case = case or self.case
        return resolve_case_access(self.db, case.id, user.id, path or f"/cases/{case.id}/profile")

    def audit_events(self) -> list[AuthAuditEvent]:
        return list(self.db.scalars(select(AuthAuditEvent)))


class InvitationTests(DelegationFixture):
    def test_owner_invites_by_email_and_token_is_only_emailed_and_stored_hashed(self) -> None:
        result = self.invite()

        self.assertEqual(result.status, "pending")
        self.assertEqual(result.operator, "party")
        token = self.token()
        stored = self.db.scalar(select(CaseDelegationInvitation))
        self.assertEqual(stored.token_hash, hash_token(token))
        self.assertNotIn(token, repr(result))
        self.assertEqual(self.sent[0][0], "lawyer@example.com")
        self.assertIn("does not verify", self.sent[0][2])
        self.assertIsNone(self.access(self.pro)[0])

    def test_only_the_owner_can_invite_and_not_oneself_or_twice(self) -> None:
        with self.assertRaises(HTTPException) as raised:
            self.invite(user=self.stranger)
        self.assertEqual(raised.exception.status_code, 403)
        with self.assertRaises(HTTPException) as raised:
            self.invite(email="party@example.com")
        self.assertEqual(raised.exception.status_code, 422)
        self.invite()
        with self.assertRaises(HTTPException) as raised:
            self.invite(email="someone@example.com")
        self.assertEqual(raised.exception.status_code, 409)
        self.assertEqual(len(self.sent), 1)

    def test_email_failure_creates_no_invitation(self) -> None:
        with patch("app.case_delegation._send_email", side_effect=OSError("smtp down")):
            with self.assertRaises(HTTPException) as raised:
                self.invite()
        self.assertEqual(raised.exception.status_code, 503)
        self.assertEqual(self.db.scalars(select(CaseDelegationInvitation)).all(), [])

    def test_expired_invitation_cannot_be_accepted_and_can_be_replaced(self) -> None:
        self.invite()
        token = self.token()
        invitation = self.db.scalar(select(CaseDelegationInvitation))
        invitation.expires_at = datetime.now(UTC) - timedelta(minutes=1)
        self.db.commit()
        with self.assertRaises(HTTPException) as raised:
            self.accept(self.pro, token)
        self.assertEqual(raised.exception.status_code, 404)
        self.assertEqual(self.invite().status, "pending")


class AcceptanceTests(DelegationFixture):
    def test_acceptance_requires_matching_professional_and_valid_token(self) -> None:
        self.invite()
        token = self.token()
        for user, supplied in (
            (self.stranger, token),
            (self.pro, "x" * 43),
            (self.party, token),
        ):
            with self.assertRaises(HTTPException) as raised:
                self.accept(user, supplied)
            self.assertEqual(raised.exception.status_code, 404)
        self.assertIsNone(self.access(self.pro)[0])
        party_membership, denial = self.access(self.party)
        self.assertIsNotNone(party_membership)
        self.assertIsNone(denial)
        self.assertEqual(
            sum(1 for event in self.audit_events() if event.outcome == "denied"), 3
        )

    def test_party_account_type_cannot_accept_even_with_matching_email(self) -> None:
        self.pro.account_type = "party"
        self.db.commit()
        self.invite()
        with self.assertRaises(HTTPException):
            self.accept(self.pro)

    def test_accepting_makes_delegate_the_only_operator(self) -> None:
        self.invite()
        accepted = self.accept(self.pro)

        self.assertEqual(accepted.case_id, self.case.id)
        delegate_membership, denial = self.access(self.pro)
        self.assertEqual(delegate_membership.role, "delegate")
        self.assertIsNone(denial)
        owner_membership, owner_denial = self.access(self.party)
        self.assertIsNone(owner_membership)
        self.assertEqual(owner_denial[0], 409)
        _, delegation_denial = self.access(
            self.party, path=f"/cases/{self.case.id}/delegation"
        )
        self.assertIsNone(delegation_denial)
        active = self.db.scalars(
            select(CaseMembership).where(
                CaseMembership.case_id == self.case.id,
                CaseMembership.revoked_at.is_(None),
                CaseMembership.suspended_at.is_(None),
            )
        ).all()
        self.assertEqual([m.user_id for m in active], [self.pro.id])

    def test_token_is_single_use(self) -> None:
        self.invite()
        token = self.token()
        self.accept(self.pro, token)
        with self.assertRaises(HTTPException):
            self.accept(self.pro, token)

    def test_database_rejects_two_concurrent_operators(self) -> None:
        self.db.add(CaseMembership(case_id=self.case.id, user_id=self.pro.id, role="delegate"))
        with self.assertRaises(IntegrityError):
            self.db.flush()
        self.db.rollback()

    def test_delegate_cannot_manage_delegation_and_other_cases_stay_isolated(self) -> None:
        self.invite()
        self.accept(self.pro)
        with self.assertRaises(HTTPException) as raised:
            get_delegation(self.case.id, self.request(self.pro), Response(), self.db)
        self.assertEqual(raised.exception.status_code, 403)
        with self.assertRaises(HTTPException):
            self.revoke(self.pro)
        other_case = self._case(self.other_party)
        membership, denial = self.access(self.pro, other_case)
        self.assertIsNone(membership)
        self.assertEqual(denial[0], 404)

    def test_professional_operates_multiple_client_cases_without_owning_them(self) -> None:
        second = self._case(self.other_party)
        self.invite()
        self.accept(self.pro)
        self.invite(case=second, user=self.other_party)
        self.accept(self.pro)

        roles = self.db.scalars(
            select(CaseMembership.role).where(CaseMembership.user_id == self.pro.id)
        ).all()
        self.assertEqual(roles, ["delegate", "delegate"])
        with self.assertRaises(HTTPException) as raised:
            require_active_case_slot(self.db, self.pro.id)
        self.assertEqual(raised.exception.status_code, 403)


class RevocationTests(DelegationFixture):
    def test_revoking_immediately_removes_delegate_and_restores_party(self) -> None:
        self.invite()
        self.accept(self.pro)
        result = self.revoke()

        self.assertEqual(result.status, "none")
        membership, denial = self.access(self.pro)
        self.assertIsNone(membership)
        self.assertEqual(denial[0], 404)
        owner_membership, owner_denial = self.access(self.party)
        self.assertIsNotNone(owner_membership)
        self.assertIsNone(owner_denial)
        with self.assertRaises(HTTPException):
            self.accept(self.pro)

    def test_pending_invitation_can_be_revoked_and_token_dies(self) -> None:
        self.invite()
        token = self.token()
        self.revoke()
        with self.assertRaises(HTTPException):
            self.accept(self.pro, token)
        with self.assertRaises(HTTPException) as raised:
            self.revoke()
        self.assertEqual(raised.exception.status_code, 404)

    def test_party_can_reinvite_the_same_delegate_after_revocation(self) -> None:
        self.invite()
        self.accept(self.pro)
        self.revoke()
        self.invite()
        self.accept(self.pro)
        membership, _ = self.access(self.pro)
        self.assertEqual(membership.role, "delegate")

    def test_delegation_paths_remain_writable_on_closed_cases(self) -> None:
        self.case.status = "finalized"
        self.assertTrue(lifecycle_write_allowed(self.case, f"/cases/{self.case.id}/delegation"))
        self.assertFalse(lifecycle_write_allowed(self.case, f"/cases/{self.case.id}/profile"))


class AuditTests(DelegationFixture):
    def test_events_record_ids_only_without_email_or_token(self) -> None:
        self.invite()
        token = self.token()
        self.accept(self.pro)
        self.revoke()

        events = self.audit_events()
        self.assertEqual(
            {event.event_type for event in events},
            {"case_delegation_invited", "case_delegation_accepted", "case_delegation_revoked"},
        )
        dump = repr([(e.event_type, e.outcome, e.context) for e in events])
        self.assertNotIn(token, dump)
        self.assertNotIn("example.com", dump)


class PartyCaseLimitTests(DelegationFixture):
    def test_party_cannot_create_a_second_case_regardless_of_status_or_plan(self) -> None:
        self.case.status = "finalized"
        self.case.closed_at = datetime.now(UTC)
        self.db.commit()
        with self.assertRaises(HTTPException) as raised:
            require_active_case_slot(self.db, self.party.id)
        self.assertEqual(raised.exception.status_code, 409)

    def test_party_without_a_case_may_create_one(self) -> None:
        user = User(email="new@example.com", status="active")
        self.db.add(user)
        self.db.commit()
        self.assertIs(require_active_case_slot(self.db, user.id), user)

    def test_being_a_delegate_does_not_count_against_a_party_account(self) -> None:
        self.other_party.account_type = "party"
        self.db.commit()
        self.assertIs(require_active_case_slot(self.db, self.other_party.id), self.other_party)
