import hashlib
import json
from copy import deepcopy
from datetime import UTC, datetime
from uuid import UUID

from app.models import SettlementNegotiationAttempt, SettlementProposalVersion

SNAPSHOT_SCHEMA_VERSION = 1
# Names the policy that produced the debit recorded with the finalized version. It is
# descriptive only: replacing the entitlement policy must not change snapshot semantics.
CHARGE_POLICY_DOCUMENT_CREDIT_PER_VERSION = "document_credit_per_version"


def is_finalized(attempt: object) -> bool:
    return getattr(attempt, "finalized_at", None) is not None


def _digest(value: object) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def build_finalization_snapshot(
    attempt: SettlementNegotiationAttempt,
    selection: object,
    version: SettlementProposalVersion,
    *,
    finalized_at: datetime,
    user_id: UUID,
) -> dict:
    snapshot = deepcopy(attempt.snapshot_json)
    snapshot["scenario"] = {
        "run_id": str(selection.run_id),
        "scenario_id": selection.scenario_id,
        "objective": attempt.snapshot_json.get("scenario", {}).get("objective"),
        "axes": deepcopy(attempt.editable_state_json.get("scenario_assumptions")),
        "result": deepcopy(version.scenario_result_json),
    }
    snapshot["schema_version"] = SNAPSHOT_SCHEMA_VERSION
    snapshot["negotiation"] = deepcopy(attempt.editable_state_json)
    snapshot["proposal_terms"] = deepcopy(version.terms_json)
    snapshot["proposal_version"] = {
        "id": str(version.id),
        "ordinal": version.version_ordinal,
        "request_sha256": version.request_sha256,
        "docx_sha256": hashlib.sha256(version.docx_content).hexdigest(),
        "xlsx_sha256": hashlib.sha256(version.xlsx_content).hexdigest(),
    }
    snapshot["entitlement_charge"] = {
        "policy": CHARGE_POLICY_DOCUMENT_CREDIT_PER_VERSION,
        "credit_cost": version.credit_cost,
    }
    snapshot["attempt_ordinal"] = attempt.attempt_ordinal
    snapshot["finalized_at"] = finalized_at.isoformat()
    snapshot["finalized_by_user_id_snapshot"] = str(user_id)
    snapshot["externally_sent"] = False
    snapshot["snapshot_sha256"] = _digest(snapshot)
    return snapshot


def finalize_attempt(
    attempt: SettlementNegotiationAttempt,
    selection: object,
    version: SettlementProposalVersion,
    *,
    user_id: UUID,
) -> None:
    finalized_at = datetime.now(UTC)
    attempt.finalized_snapshot_json = build_finalization_snapshot(
        attempt, selection, version, finalized_at=finalized_at, user_id=user_id
    )
    attempt.finalized_version_ordinal = version.version_ordinal
    attempt.finalized_by_user_id_snapshot = user_id
    attempt.finalized_at = finalized_at
    attempt.revision += 1
