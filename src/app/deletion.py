import logging
from datetime import UTC, datetime
from uuid import NAMESPACE_URL, UUID, uuid4, uuid5

from fastapi import APIRouter, Depends, HTTPException, Response
from pydantic import BaseModel, ConfigDict, model_validator
from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.auth_routes import require_current_user
from app.database import Base, get_db
from app.models import (
    AuthAuditEvent,
    Case,
    CaseDelegationInvitation,
    CaseMembership,
    DeletionTombstone,
    Document,
    DocumentCreditLedgerEntry,
    MaterialImportItem,
    User,
)
from app.storage import ObjectStorage

logger = logging.getLogger(__name__)
router = APIRouter(tags=["permanent deletion"])
storage = ObjectStorage()

CASE_CONFIRMATION = "DELETE CASE"
MATERIAL_CONFIRMATION = "DELETE MATERIAL"
ACCOUNT_CONFIRMATION = "DELETE MY ACCOUNT"


class PermanentDeletionConfirmation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    confirmation: str

    @model_validator(mode="after")
    def confirmation_is_exact(self):
        if self.confirmation not in {
            CASE_CONFIRMATION,
            MATERIAL_CONFIRMATION,
            ACCOUNT_CONFIRMATION,
        }:
            raise ValueError("The permanent-deletion confirmation phrase is invalid.")
        return self


class AccountDeletionRequest(PermanentDeletionConfirmation):
    password: str
    totp_code: str | None = None

    @model_validator(mode="after")
    def account_confirmation_is_exact(self):
        if self.confirmation != ACCOUNT_CONFIRMATION:
            raise ValueError(f'Type "{ACCOUNT_CONFIRMATION}" to confirm account deletion.')
        return self


def scope_tombstone(
    db: Session,
    scope_type: str,
    scope_id: UUID,
) -> DeletionTombstone | None:
    tombstone = db.scalar(
        select(DeletionTombstone).where(
            DeletionTombstone.scope_type == scope_type,
            DeletionTombstone.scope_id == scope_id,
        )
    )
    return tombstone if isinstance(tombstone, DeletionTombstone) else None


def scope_is_tombstoned(db: Session, scope_type: str, scope_id: UUID) -> bool:
    return scope_tombstone(db, scope_type, scope_id) is not None


def import_item_tombstone_id(batch_id: UUID, item_id: UUID) -> UUID:
    return uuid5(NAMESPACE_URL, f"casework:material-import:{batch_id}:{item_id}")


def require_scope_active(db: Session, scope_type: str, scope_id: UUID) -> None:
    if scope_is_tombstoned(db, scope_type, scope_id):
        raise HTTPException(status_code=410, detail="This data has been permanently deleted.")


def _owner_case(db: Session, case_id: UUID, user_id: UUID, *, lock: bool = False) -> Case:
    case = db.get(Case, case_id, with_for_update=lock)
    if case is None:
        raise HTTPException(status_code=404, detail="Case not found.")
    membership = db.scalar(
        select(CaseMembership).where(
            CaseMembership.case_id == case_id,
            CaseMembership.user_id == user_id,
            CaseMembership.role == "owner",
            CaseMembership.revoked_at.is_(None),
            CaseMembership.suspended_at.is_(None),
        )
    )
    if membership is None:
        raise HTTPException(status_code=403, detail="Only the case owner can permanently delete it.")
    return case


def _get_or_create_tombstone(
    db: Session,
    scope_type: str,
    scope_id: UUID,
    initiated_by: UUID,
    object_keys: list[str],
) -> DeletionTombstone:
    tombstone = db.scalar(
        select(DeletionTombstone)
        .where(
            DeletionTombstone.scope_type == scope_type,
            DeletionTombstone.scope_id == scope_id,
        )
        .with_for_update()
    )
    if tombstone is not None:
        if tombstone.initiated_by != initiated_by:
            raise HTTPException(status_code=403, detail="Deletion was initiated by another account.")
        return tombstone
    tombstone = DeletionTombstone(
        scope_type=scope_type,
        scope_id=scope_id,
        initiated_by=initiated_by,
        status="pending",
        object_keys=object_keys,
    )
    db.add(tombstone)
    return tombstone


def _persist_deletion_barrier(db: Session, action: str) -> None:
    try:
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Could not establish the permanent-deletion barrier (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail=f"{action} could not be started. Please retry.",
        ) from error


def _purge_objects(object_keys: list[str], object_storage: ObjectStorage, action: str) -> None:
    try:
        purge = getattr(object_storage, "delete_all_versions")
        for key in object_keys:
            purge(key)
    except Exception as error:
        logger.error("Permanent %s object purge failed (%s).", action, type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail=f"{action.capitalize()} is incomplete because stored object versions could not be purged. Please retry.",
        ) from error


def _complete_tombstone(db: Session, tombstone: DeletionTombstone) -> None:
    tombstone.status = "completed"
    tombstone.completed_at = datetime.now(UTC)
    tombstone.object_keys = []


def delete_document_scope(
    db: Session,
    user: User,
    case_id: UUID,
    document_id: UUID,
    object_storage: ObjectStorage,
) -> bool:
    existing_tombstone = scope_tombstone(db, "document", document_id)
    if existing_tombstone is not None:
        if existing_tombstone.initiated_by != user.id:
            raise HTTPException(status_code=403, detail="Deletion was initiated by another account.")
        if existing_tombstone.status == "completed":
            return True

    case = _owner_case(db, case_id, user.id, lock=True)
    require_scope_active(db, "case", case.id)
    document = db.get(Document, document_id, with_for_update=True)
    if document is None or document.case_id != case_id:
        raise HTTPException(status_code=404, detail="Case material not found.")
    tombstone = _get_or_create_tombstone(
        db,
        "document",
        document.id,
        user.id,
        [document.object_key],
    )
    import_item_tombstones = [
        _get_or_create_tombstone(
            db,
            "import_item",
            import_item_tombstone_id(item.batch_id, item.item_id),
            user.id,
            [],
        )
        for item in db.scalars(
            select(MaterialImportItem).where(MaterialImportItem.document_id == document.id)
        )
    ]
    _persist_deletion_barrier(db, "Material deletion")
    if tombstone.status == "completed":
        return True

    _purge_objects(tombstone.object_keys, object_storage, "material deletion")
    try:
        db.delete(document)
        _complete_tombstone(db, tombstone)
        for import_tombstone in import_item_tombstones:
            _complete_tombstone(db, import_tombstone)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Material metadata cleanup failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Material deletion is incomplete. Please retry to finish cleanup.",
        ) from error
    return True


def _case_object_keys(db: Session, case_id: UUID) -> list[str]:
    return list(
        db.scalars(
            select(Document.object_key)
            .where(Document.case_id == case_id)
            .order_by(Document.object_key)
        )
    )


def _delete_case_rows(db: Session, case: Case) -> None:
    db.execute(
        delete(DocumentCreditLedgerEntry).where(DocumentCreditLedgerEntry.case_id == case.id)
    )
    db.delete(case)


def delete_case_scope(
    db: Session,
    user: User,
    case_id: UUID,
    object_storage: ObjectStorage,
) -> bool:
    existing_tombstone = scope_tombstone(db, "case", case_id)
    if existing_tombstone is not None:
        if existing_tombstone.initiated_by != user.id:
            raise HTTPException(status_code=403, detail="Deletion was initiated by another account.")
        if existing_tombstone.status == "completed":
            return True

    case = _owner_case(db, case_id, user.id, lock=True)
    tombstone = _get_or_create_tombstone(
        db,
        "case",
        case_id,
        user.id,
        _case_object_keys(db, case_id),
    )
    _persist_deletion_barrier(db, "Case deletion")
    if tombstone.status == "completed":
        return True

    _purge_objects(tombstone.object_keys, object_storage, "case deletion")
    try:
        case = db.get(Case, case_id, with_for_update=True)
        if case is not None:
            _delete_case_rows(db, case)
        _complete_tombstone(db, tombstone)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Case database cleanup failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Case deletion is incomplete. Please retry to finish cleanup.",
        ) from error
    return True


def _anonymize_account_snapshots(db: Session, user_id: UUID) -> None:
    for table in Base.metadata.tables.values():
        for column_name in ("user_id_snapshot", "finalized_by_user_id_snapshot"):
            column = table.c.get(column_name)
            if column is None:
                continue
            db.execute(
                update(table)
                .where(column == user_id)
                .values({column_name: uuid4() if column.nullable else uuid4()})
            )


def _anonymize_account_invitations(db: Session, user: User) -> None:
    now = datetime.now(UTC)
    db.execute(
        update(CaseDelegationInvitation)
        .where(
            CaseDelegationInvitation.owner_user_id != user.id,
            CaseDelegationInvitation.invitee_email == user.email,
        )
        .values(
            invitee_email=f"deleted-{user.id}@invalid.invalid",
            status="revoked",
            revoked_at=now,
        )
    )


def delete_account_scope(db: Session, user: User, object_storage: ObjectStorage) -> bool:
    account_tombstone = scope_tombstone(db, "account", user.id)
    if account_tombstone is not None:
        if account_tombstone.initiated_by != user.id:
            raise HTTPException(status_code=403, detail="Deletion was initiated by another account.")
        if account_tombstone.status == "completed":
            return True

    locked_user = db.get(User, user.id, with_for_update=True)
    if locked_user is None:
        return account_tombstone is not None and account_tombstone.status == "completed"
    owned_case_ids = list(
        db.scalars(
            select(CaseMembership.case_id)
            .where(
                CaseMembership.user_id == user.id,
                CaseMembership.role == "owner",
                CaseMembership.revoked_at.is_(None),
            )
            .order_by(CaseMembership.case_id)
        )
    )
    owned_cases = [
        case
        for case_id in owned_case_ids
        if (case := db.get(Case, case_id, with_for_update=True)) is not None
    ]
    account_tombstone = _get_or_create_tombstone(
        db, "account", user.id, user.id, []
    )
    case_tombstones = [
        _get_or_create_tombstone(
            db,
            "case",
            case.id,
            user.id,
            _case_object_keys(db, case.id),
        )
        for case in owned_cases
    ]
    locked_user.status = "disabled"
    _persist_deletion_barrier(db, "Account deletion")

    for tombstone in case_tombstones:
        if tombstone.status == "pending":
            _purge_objects(tombstone.object_keys, object_storage, "account deletion")

    try:
        for case_id in owned_case_ids:
            case = db.get(Case, case_id, with_for_update=True)
            if case is not None:
                _delete_case_rows(db, case)
        db.execute(
            delete(DocumentCreditLedgerEntry).where(
                DocumentCreditLedgerEntry.user_id == user.id
            )
        )
        _anonymize_account_snapshots(db, user.id)
        _anonymize_account_invitations(db, locked_user)
        db.execute(delete(AuthAuditEvent).where(AuthAuditEvent.user_id == user.id))
        for tombstone in case_tombstones:
            _complete_tombstone(db, tombstone)
        db.delete(locked_user)
        _complete_tombstone(db, account_tombstone)
        db.commit()
    except SQLAlchemyError as error:
        db.rollback()
        logger.error("Account database cleanup failed (%s).", type(error).__name__)
        raise HTTPException(
            status_code=503,
            detail="Account deletion is incomplete. Please retry to finish cleanup.",
        ) from error
    return True


@router.delete("/cases/{case_id}/permanent-deletion", status_code=204)
def permanently_delete_case(
    case_id: UUID,
    payload: PermanentDeletionConfirmation,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Response:
    if payload.confirmation != CASE_CONFIRMATION:
        raise HTTPException(status_code=422, detail=f'Type "{CASE_CONFIRMATION}" to confirm case deletion.')
    delete_case_scope(db, user, case_id, storage)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.delete(
    "/cases/{case_id}/materials/{document_id}/permanent-deletion",
    status_code=204,
)
def permanently_delete_material(
    case_id: UUID,
    document_id: UUID,
    payload: PermanentDeletionConfirmation,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Response:
    if payload.confirmation != MATERIAL_CONFIRMATION:
        raise HTTPException(
            status_code=422,
            detail=f'Type "{MATERIAL_CONFIRMATION}" to confirm material deletion.',
        )
    delete_document_scope(db, user, case_id, document_id, storage)
    return Response(status_code=204, headers={"Cache-Control": "no-store"})


@router.delete("/api/v1/account/permanent-deletion", status_code=204)
def permanently_delete_account(
    payload: AccountDeletionRequest,
    response: Response,
    user: User = Depends(require_current_user),
    db: Session = Depends(get_db),
) -> Response:
    from app.auth import verify_password
    from app.auth_routes import _verify_second_factor
    from app.models import TotpCredential

    if user.password_hash is None or not verify_password(user.password_hash, payload.password):
        raise HTTPException(status_code=401, detail="Recent account verification is required.")
    if user.mfa_enabled:
        credential = db.scalar(
            select(TotpCredential).where(
                TotpCredential.user_id == user.id,
                TotpCredential.pending.is_(False),
                TotpCredential.revoked_at.is_(None),
            )
        )
        if (
            credential is None
            or payload.totp_code is None
            or not _verify_second_factor(db, user, credential, payload.totp_code)
        ):
            raise HTTPException(status_code=401, detail="Recent account verification is required.")
    delete_account_scope(db, user, storage)
    from app.auth_routes import clear_auth_cookies

    clear_auth_cookies(response)
    response.headers["Cache-Control"] = "no-store"
    response.status_code = 204
    return response
