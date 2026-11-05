import logging
import smtplib
from datetime import UTC, datetime, timedelta
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth import hash_token, normalize_email, random_token
from app.auth_routes import (
    _audit,
    _rate_limit,
    _require_email_config,
    _send_email,
    require_current_user,
)
from app.database import get_db
from app.models import Case, CaseDelegationInvitation, CaseMembership, User

logger = logging.getLogger(__name__)
router = APIRouter(tags=["case delegation"])

INVITATION_LIFETIME = timedelta(days=7)
NO_LEGAL_VERIFICATION_NOTICE = (
    "Delegation is the party's explicit permission only. It does not verify the "
    "delegate's identity, license, or legal authority."
)
_DELEGATION_SUFFIX = "/delegation"
_OPEN_STATUSES = ("pending", "accepted")


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo else value.replace(tzinfo=UTC)


def is_delegation_path(path: str, case_id: UUID) -> bool:
    return path.rstrip("/") == f"/cases/{case_id}{_DELEGATION_SUFFIX}"


def resolve_case_access(
    db: Session, case_id: UUID, user_id: UUID, path: str
) -> tuple[CaseMembership | None, tuple[int, str] | None]:
    """Return the caller's usable membership, or the HTTP denial to send."""
    membership = db.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == user_id,
            CaseMembership.revoked_at.is_(None),
        )
    )
    if membership is None:
        return None, (404, "Case not found.")
    if membership.suspended_at is not None and not is_delegation_path(path, case_id):
        return None, (
            409,
            "This case is currently operated by your designated delegate. "
            "Revoke the delegation to resume operating it.",
        )
    return membership, None


class DelegationInvite(BaseModel):
    email: EmailStr


class DelegationAccept(BaseModel):
    token: str = Field(min_length=20, max_length=128)


class DelegationRead(BaseModel):
    status: Literal["none", "pending", "accepted"]
    operator: Literal["party", "delegate"]
    invitee_email: str | None = None
    expires_at: datetime | None = None
    notice: str = NO_LEGAL_VERIFICATION_NOTICE


class DelegationAccepted(BaseModel):
    case_id: UUID
    role: Literal["delegate"] = "delegate"
    notice: str = NO_LEGAL_VERIFICATION_NOTICE


def _no_store(response: Response) -> None:
    response.headers["Cache-Control"] = "no-store"


def _owner_membership(db: Session, case_id: UUID, user_id: UUID) -> CaseMembership:
    membership = db.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == user_id,
            CaseMembership.role == "owner",
            CaseMembership.revoked_at.is_(None),
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Only the party who owns this case can manage delegation.")
    return membership


def _open_invitation(db: Session, case_id: UUID) -> CaseDelegationInvitation | None:
    invitation = db.scalar(
        select(CaseDelegationInvitation)
        .where(
            CaseDelegationInvitation.case_id == case_id,
            CaseDelegationInvitation.status.in_(_OPEN_STATUSES),
        )
        .with_for_update()
    )
    if (
        invitation is not None
        and invitation.status == "pending"
        and _aware(invitation.expires_at) <= datetime.now(UTC)
    ):
        invitation.status = "expired"
        db.flush()
        return None
    return invitation


def _commit(db: Session) -> None:
    try:
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="The case delegation changed. Reload and try again.") from error
    except SQLAlchemyError as error:
        db.rollback()
        logger.exception("Case delegation update failed.")
        raise HTTPException(status_code=503, detail="Delegation could not be updated. Please try again.") from error


def _read(invitation: CaseDelegationInvitation | None) -> DelegationRead:
    if invitation is None:
        return DelegationRead(status="none", operator="party")
    return DelegationRead(
        status=invitation.status,
        operator="delegate" if invitation.status == "accepted" else "party",
        invitee_email=invitation.invitee_email,
        expires_at=invitation.expires_at,
    )


@router.get("/cases/{case_id}/delegation", response_model=DelegationRead)
def get_delegation(case_id: UUID, request: Request, response: Response, db: Annotated[Session, Depends(get_db)]) -> DelegationRead:
    _no_store(response)
    _owner_membership(db, case_id, request.state.user_id)
    result = _read(_open_invitation(db, case_id))
    db.commit()
    return result


@router.post("/cases/{case_id}/delegation", response_model=DelegationRead, status_code=201)
def invite_delegate(
    case_id: UUID,
    payload: DelegationInvite,
    request: Request,
    response: Response,
    db: Annotated[Session, Depends(get_db)],
) -> DelegationRead:
    _no_store(response)
    user_id = request.state.user_id
    _require_email_config()
    try:
        invitee_email = normalize_email(str(payload.email))
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    _rate_limit(db, request, "delegation-invite", str(user_id))
    owner = db.get(User, user_id)
    membership = _owner_membership(db, case_id, user_id)
    if owner is None or membership.suspended_at is not None:
        raise HTTPException(status_code=409, detail="The case is already operated by a delegate.")
    if invitee_email == normalize_email(owner.email):
        raise HTTPException(status_code=422, detail="Invite someone other than yourself.")
    if _open_invitation(db, case_id) is not None:
        raise HTTPException(status_code=409, detail="This case already has a delegate invitation. Revoke it first.")
    token = random_token()
    invitation = CaseDelegationInvitation(
        case_id=case_id,
        owner_user_id=user_id,
        invitee_email=invitee_email,
        token_hash=hash_token(token),
        status="pending",
        expires_at=datetime.now(UTC) + INVITATION_LIFETIME,
    )
    db.add(invitation)
    try:
        db.flush()
        _audit(db, "case_delegation_invited", "success", user_id, {
            "case_id": str(case_id), "invitation_id": str(invitation.id)})
        _send_email(
            invitee_email,
            "You were invited to operate a divorce case",
            "A party invited you to operate their case. Sign in with a professional "
            "account using this email address and submit this one-time code to accept: "
            f"{token}\nIt expires in 7 days. Accepting is your explicit choice; the invitation "
            "does not verify your identity or legal authority.",
        )
    except (smtplib.SMTPException, OSError) as error:
        db.rollback()
        logger.exception("Could not deliver a delegation invitation email.")
        raise HTTPException(status_code=503, detail="Invitation email could not be delivered.") from error
    except IntegrityError as error:
        db.rollback()
        raise HTTPException(status_code=409, detail="This case already has a delegate invitation.") from error
    _commit(db)
    return _read(invitation)


@router.delete("/cases/{case_id}/delegation", response_model=DelegationRead)
def revoke_delegation(
    case_id: UUID, request: Request, response: Response, db: Annotated[Session, Depends(get_db)]
) -> DelegationRead:
    _no_store(response)
    user_id = request.state.user_id
    owner_membership = _owner_membership(db, case_id, user_id)
    invitation = _open_invitation(db, case_id)
    if invitation is None:
        raise HTTPException(status_code=404, detail="No delegation to revoke.")
    now = datetime.now(UTC)
    was_accepted = invitation.status == "accepted"
    invitation.status = "revoked"
    invitation.revoked_at = now
    if was_accepted and invitation.delegate_user_id is not None:
        delegate = db.scalar(
            select(CaseMembership).where(
                CaseMembership.case_id == case_id,
                CaseMembership.user_id == invitation.delegate_user_id,
                CaseMembership.role == "delegate",
                CaseMembership.revoked_at.is_(None),
            )
        )
        if delegate is not None:
            delegate.revoked_at = now
    db.flush()
    owner_membership.suspended_at = None
    _audit(db, "case_delegation_revoked", "success", user_id, {
        "case_id": str(case_id), "invitation_id": str(invitation.id), "was_accepted": was_accepted})
    _commit(db)
    return DelegationRead(status="none", operator="party")


@router.post("/api/v1/delegations/accept", response_model=DelegationAccepted)
def accept_delegation(
    payload: DelegationAccept,
    request: Request,
    response: Response,
    user: Annotated[User, Depends(require_current_user)],
    db: Annotated[Session, Depends(get_db)],
) -> DelegationAccepted:
    _no_store(response)
    _rate_limit(db, request, "delegation-accept", str(user.id))
    invitation = db.scalar(
        select(CaseDelegationInvitation)
        .where(CaseDelegationInvitation.token_hash == hash_token(payload.token))
        .with_for_update()
    )
    now = datetime.now(UTC)
    valid = (
        invitation is not None
        and invitation.status == "pending"
        and _aware(invitation.expires_at) > now
        and user.account_type == "professional"
        and normalize_email(user.email) == invitation.invitee_email
    )
    if not valid:
        _audit(db, "case_delegation_accepted", "denied", user.id, {})
        _commit(db)
        raise HTTPException(status_code=404, detail="Invitation not found or no longer valid.")
    owner_membership = db.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == invitation.case_id,
            CaseMembership.user_id == invitation.owner_user_id,
            CaseMembership.role == "owner",
            CaseMembership.revoked_at.is_(None),
            CaseMembership.suspended_at.is_(None),
        )
    )
    if owner_membership is None or db.get(Case, invitation.case_id) is None:
        raise HTTPException(status_code=404, detail="Invitation not found or no longer valid.")
    owner_membership.suspended_at = now
    db.flush()
    delegate = db.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == invitation.case_id,
            CaseMembership.user_id == user.id,
        )
    )
    if delegate is None:
        db.add(CaseMembership(case_id=invitation.case_id, user_id=user.id, role="delegate"))
    else:
        delegate.role = "delegate"
        delegate.revoked_at = None
        delegate.suspended_at = None
        delegate.granted_at = now
    invitation.status = "accepted"
    invitation.accepted_at = now
    invitation.delegate_user_id = user.id
    _audit(db, "case_delegation_accepted", "success", user.id, {
        "case_id": str(invitation.case_id), "invitation_id": str(invitation.id)})
    _commit(db)
    return DelegationAccepted(case_id=invitation.case_id)
