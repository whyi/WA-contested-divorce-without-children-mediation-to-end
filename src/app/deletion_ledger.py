import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.deletion import (
    _anonymize_account_invitations,
    _anonymize_account_snapshots,
    _case_object_keys,
    _complete_tombstone,
    _delete_case_rows,
    _get_or_create_tombstone,
    _purge_objects,
)
from app.models import (
    AuthAuditEvent,
    Case,
    CaseMembership,
    DeletionTombstone,
    Document,
    DocumentCreditLedgerEntry,
    User,
)
from app.storage import ObjectStorage

logger = logging.getLogger(__name__)
_SUPPORTED_SCOPES = {"account", "case", "document", "import_item"}
_RECONCILIATION_ORDER = {"document": 0, "import_item": 1, "case": 2, "account": 3}


@dataclass(frozen=True)
class DeletionLedgerEntry:
    scope_type: str
    scope_id: UUID
    initiated_by: UUID
    object_keys: list[str]

    @classmethod
    def parse(cls, raw: dict[str, object]) -> "DeletionLedgerEntry":
        if raw.get("schema_version") != 1:
            raise RuntimeError("The permanent-deletion ledger contains an unsupported schema version.")
        scope_type = raw.get("scope_type")
        if scope_type not in _SUPPORTED_SCOPES:
            raise RuntimeError("The permanent-deletion ledger contains an unsupported scope.")
        try:
            object_keys = raw.get("object_keys", [])
            if not isinstance(object_keys, list) or not all(
                isinstance(key, str) for key in object_keys
            ):
                raise ValueError("Invalid object-key list.")
            return cls(
                scope_type=scope_type,
                scope_id=UUID(str(raw["scope_id"])),
                initiated_by=UUID(str(raw["initiated_by"])),
                object_keys=object_keys,
            )
        except (KeyError, ValueError) as error:
            raise RuntimeError("The permanent-deletion ledger contains an invalid entry.") from error


def initialize_deletion_ledger(db: Session, storage: ObjectStorage) -> int:
    if storage.deletion_ledger_initialized():
        raise RuntimeError("The permanent-deletion ledger is already initialized.")
    rows = db.scalars(select(DeletionTombstone).order_by(DeletionTombstone.id)).all()
    entries = [
        {
            "scope_type": row.scope_type,
            "scope_id": str(row.scope_id),
            "initiated_by": str(row.initiated_by),
            "object_keys": list(row.object_keys),
        }
        for row in rows
    ]
    storage.initialize_deletion_ledger(entries)
    logger.info("Initialized permanent-deletion ledger with %d existing tombstones.", len(entries))
    return len(entries)


def reconcile_deletion_ledger(db: Session, storage: ObjectStorage) -> int:
    entries = [
        DeletionLedgerEntry.parse(raw)
        for raw in storage.read_deletion_tombstones()
    ]
    _restore_tombstones(db, entries)
    for entry in sorted(entries, key=lambda item: _RECONCILIATION_ORDER[item.scope_type]):
        _reconcile_entry(db, storage, entry)
    logger.info("Reconciled %d permanent-deletion ledger entries.", len(entries))
    return len(entries)


def _restore_tombstones(db: Session, entries: list[DeletionLedgerEntry]) -> None:
    try:
        for entry in entries:
            tombstone = db.scalar(
                select(DeletionTombstone)
                .where(
                    DeletionTombstone.scope_type == entry.scope_type,
                    DeletionTombstone.scope_id == entry.scope_id,
                )
                .with_for_update()
            )
            if tombstone is not None:
                if tombstone.initiated_by != entry.initiated_by:
                    raise RuntimeError("The deletion ledger conflicts with a database tombstone.")
                continue
            db.add(
                DeletionTombstone(
                    scope_type=entry.scope_type,
                    scope_id=entry.scope_id,
                    initiated_by=entry.initiated_by,
                    status="pending",
                    object_keys=entry.object_keys,
                )
            )
            try:
                db.flush()
                db.commit()
            except IntegrityError:
                db.rollback()
                existing = db.scalar(
                    select(DeletionTombstone).where(
                        DeletionTombstone.scope_type == entry.scope_type,
                        DeletionTombstone.scope_id == entry.scope_id,
                    )
                )
                if existing is None or existing.initiated_by != entry.initiated_by:
                    raise
    except Exception:
        db.rollback()
        raise


def _reconcile_entry(
    db: Session,
    storage: ObjectStorage,
    entry: DeletionLedgerEntry,
) -> None:
    tombstone = db.scalar(
        select(DeletionTombstone)
        .where(
            DeletionTombstone.scope_type == entry.scope_type,
            DeletionTombstone.scope_id == entry.scope_id,
        )
        .with_for_update()
    )
    if tombstone is None:
        raise RuntimeError("A permanent-deletion tombstone could not be restored.")
    if tombstone.status == "completed":
        db.commit()
        return
    tombstone.object_keys = sorted(set(tombstone.object_keys) | set(entry.object_keys))

    if entry.scope_type == "document":
        _reconcile_document(db, storage, tombstone)
    elif entry.scope_type == "case":
        _reconcile_case(db, storage, tombstone)
    elif entry.scope_type == "account":
        _reconcile_account(db, storage, tombstone)
    else:
        tombstone.status = "completed"
        tombstone.completed_at = datetime.now(UTC)
        tombstone.object_keys = []
        db.commit()


def _reconcile_document(
    db: Session,
    storage: ObjectStorage,
    tombstone: DeletionTombstone,
) -> None:
    document = db.get(Document, tombstone.scope_id, with_for_update=True)
    object_keys = set(tombstone.object_keys)
    if document is not None:
        object_keys.add(document.object_key)
    _purge_objects(sorted(object_keys), storage, "restore reconciliation")
    if document is not None:
        db.delete(document)
    _complete_tombstone(db, tombstone)
    db.commit()


def _reconcile_case(
    db: Session,
    storage: ObjectStorage,
    tombstone: DeletionTombstone,
) -> None:
    case = db.get(Case, tombstone.scope_id, with_for_update=True)
    object_keys = set(tombstone.object_keys)
    if case is not None:
        object_keys.update(_case_object_keys(db, case.id))
    _purge_objects(sorted(object_keys), storage, "restore reconciliation")
    if case is not None:
        _delete_case_rows(db, case)
    _complete_tombstone(db, tombstone)
    db.commit()


def _reconcile_account(
    db: Session,
    storage: ObjectStorage,
    tombstone: DeletionTombstone,
) -> None:
    user = db.get(User, tombstone.scope_id, with_for_update=True)
    if user is not None:
        owned_case_ids = db.scalars(
            select(CaseMembership.case_id)
            .where(
                CaseMembership.user_id == user.id,
                CaseMembership.role == "owner",
                CaseMembership.revoked_at.is_(None),
            )
            .order_by(CaseMembership.case_id)
        ).all()
        for case_id in owned_case_ids:
            case = db.get(Case, case_id, with_for_update=True)
            if case is None:
                continue
            case_tombstone = _get_or_create_tombstone(
                db,
                "case",
                case.id,
                user.id,
                _case_object_keys(db, case.id),
            )
            db.flush()
            _purge_objects(
                case_tombstone.object_keys,
                storage,
                "restore reconciliation",
            )
            _delete_case_rows(db, case)
            _complete_tombstone(db, case_tombstone)
        db.execute(
            delete(DocumentCreditLedgerEntry).where(
                DocumentCreditLedgerEntry.user_id == user.id
            )
        )
        _anonymize_account_snapshots(db, user.id)
        _anonymize_account_invitations(db, user)
        db.execute(delete(AuthAuditEvent).where(AuthAuditEvent.user_id == user.id))
        db.delete(user)
    _complete_tombstone(db, tombstone)
    db.commit()


def initialize_from_environment() -> int:
    from app.database import SessionLocal

    storage = ObjectStorage()
    with SessionLocal() as db:
        return initialize_deletion_ledger(db, storage)


def reconcile_from_environment() -> int:
    from app.database import SessionLocal

    storage = ObjectStorage()
    storage.check_deletion_ledger_ready()
    with SessionLocal() as db:
        return reconcile_deletion_ledger(db, storage)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Manage permanent-deletion restore protection.")
    parser.add_argument("command", choices=("initialize", "reconcile"))
    command = parser.parse_args().command
    if command == "initialize":
        count = initialize_from_environment()
        print(f"Initialized permanent-deletion ledger with {count} existing tombstones.")
    else:
        count = reconcile_from_environment()
        print(f"Reconciled {count} permanent-deletion ledger entries.")
