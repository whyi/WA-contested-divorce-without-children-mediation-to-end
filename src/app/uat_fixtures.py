import argparse
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import Settings, get_settings
from app.database import SessionLocal
from app.deletion import delete_case_scope, scope_tombstone
from app.models import Case, CaseMembership, OwnerBetaFixtureRegistry, User
from app.storage import ObjectStorage

RESET_CONFIRMATION = "RESET OWNER-BETA UAT CASE"


def track_owner_beta_fixture_case(
    db: Session,
    user_id: UUID,
    case: Case,
    settings: Settings | None = None,
) -> None:
    active_settings = settings or get_settings()
    if not active_settings.owner_beta_fixture_reset_enabled:
        return
    owner_email = str(active_settings.owner_beta_email or "").strip().casefold()
    user = db.get(User, user_id)
    if user is None or user.email.strip().casefold() != owner_email:
        raise HTTPException(status_code=403, detail="Only the configured UAT owner may create this case.")

    registry = db.get(OwnerBetaFixtureRegistry, user_id, with_for_update=True)
    if registry is None:
        db.add(OwnerBetaFixtureRegistry(owner_user_id=user_id, case_id=case.id))
        return
    if registry.case_id is not None and registry.case_id != case.id:
        raise HTTPException(
            status_code=409,
            detail="The owner-beta UAT case registry is inconsistent; contact the operator.",
        )
    registry.case_id = case.id


def reset_owner_beta_case(
    db: Session,
    settings: Settings,
    object_storage: ObjectStorage,
    confirmation: str,
) -> UUID | None:
    if confirmation != RESET_CONFIRMATION:
        raise ValueError(f'Type "{RESET_CONFIRMATION}" to confirm the permanent UAT case reset.')
    reset_errors = settings.owner_beta_fixture_reset_errors()
    if reset_errors:
        raise RuntimeError(
            "Refusing UAT case reset because deployment identity checks failed: "
            + ", ".join(reset_errors)
        )
    readiness_errors = settings.owner_beta_readiness_errors()
    if readiness_errors:
        raise RuntimeError(
            "Refusing UAT case reset because owner-beta readiness checks failed: "
            + ", ".join(readiness_errors)
        )
    object_storage.check_ready()

    owner_email = str(settings.owner_beta_email or "").strip().casefold()
    owner = db.scalar(
        select(User)
        .where(func.lower(User.email) == owner_email)
        .with_for_update()
    )
    if owner is None or owner.status != "active" or owner.account_type != "party":
        raise RuntimeError("The configured owner account is not an active party account.")
    if scope_tombstone(db, "account", owner.id) is not None:
        raise RuntimeError("The configured owner account has a permanent-deletion record.")

    memberships = db.scalars(
        select(CaseMembership)
        .where(
            CaseMembership.user_id == owner.id,
            CaseMembership.role == "owner",
            CaseMembership.revoked_at.is_(None),
        )
        .with_for_update()
    ).all()
    if any(membership.suspended_at is not None for membership in memberships):
        raise RuntimeError("The owner's case access is suspended; refusing to reset it.")

    case_ids = {membership.case_id for membership in memberships}
    cases = [case for case_id in case_ids if (case := db.get(Case, case_id)) is not None]
    if len(cases) != len(case_ids):
        raise RuntimeError("The owner case membership is inconsistent; refusing to reset it.")
    if len(cases) > 1:
        raise RuntimeError("The owner account has multiple cases; refusing to reset them.")

    registry = db.scalar(
        select(OwnerBetaFixtureRegistry)
        .where(OwnerBetaFixtureRegistry.owner_user_id == owner.id)
        .with_for_update()
    )
    if registry is None:
        if cases:
            raise RuntimeError(
                "The existing case was not registered as UAT data; refusing to delete it."
            )
        return None
    if registry.fixture_version != 1:
        raise RuntimeError("The owner-beta UAT case registry version is unsupported.")
    if registry.case_id is None:
        if cases:
            raise RuntimeError(
                "An unregistered owner case exists; refusing to delete it."
            )
        return None
    if len(cases) != 1 or cases[0].id != registry.case_id:
        raise RuntimeError(
            "The registered UAT case does not match the owner's active case; refusing to reset it."
        )

    case_id = registry.case_id
    delete_case_scope(db, owner, case_id, object_storage)
    if db.get(Case, case_id) is not None:
        raise RuntimeError(
            "The registered UAT case remains in the database after deletion; refusing to clear its registry."
        )
    db.expire_all()
    registry = db.get(OwnerBetaFixtureRegistry, owner.id)
    if registry is None:
        raise RuntimeError("The owner-beta UAT case registry disappeared during reset.")
    registry.case_id = None
    db.commit()
    return case_id


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Permanently remove the registered synthetic owner-beta UAT case."
    )
    parser.add_argument("--confirmation", required=True)
    args = parser.parse_args(argv)
    if args.confirmation != RESET_CONFIRMATION:
        parser.error(f'Type "{RESET_CONFIRMATION}" to confirm the permanent UAT case reset.')

    settings = get_settings()
    storage = ObjectStorage(settings)
    with SessionLocal() as db:
        deleted_case_id = reset_owner_beta_case(
            db,
            settings,
            storage,
            args.confirmation,
        )
    if deleted_case_id is None:
        print("The owner's empty UAT baseline is already active; no case data was changed.")
    else:
        print(
            "The registered synthetic UAT case was permanently deleted and the owner account "
            "was preserved. The clean baseline is ready for a new case."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
