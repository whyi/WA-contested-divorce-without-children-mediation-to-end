from copy import deepcopy
from typing import Any


_BASELINE_UNAVAILABLE = (
    "No explicit per-asset starting baseline is persisted for this attempt."
)
_SCENARIO_UNAVAILABLE = "A complete saved scenario result is unavailable."


def _integer(value: object) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _asset_rows(snapshot: dict) -> list[dict[str, str]]:
    assets: dict[str, dict[str, str]] = {}
    for entry in snapshot.get("settlement_ledger") or []:
        if not isinstance(entry, dict):
            continue
        asset_id = entry.get("asset_id")
        if not isinstance(asset_id, str):
            continue
        assets.setdefault(
            asset_id,
            {
                "asset_id": asset_id,
                "asset_name": str(entry.get("asset_name") or "Unnamed asset"),
                "asset_kind": str(entry.get("asset_kind") or "unknown"),
            },
        )
    return list(assets.values())


def _recorded_values(
    assets: list[dict[str, str]],
    values: object,
    *,
    value_key: str,
) -> tuple[bool, list[dict[str, Any]]]:
    if not isinstance(values, list):
        values = []
    records: dict[str, list[int]] = {}
    for item in values:
        if not isinstance(item, dict):
            continue
        asset_id = item.get("asset_id")
        amount = _integer(item.get(value_key))
        if isinstance(asset_id, str) and amount is not None:
            records.setdefault(asset_id, []).append(amount)
    known_asset_ids = {asset["asset_id"] for asset in assets}
    available = any(asset_id in known_asset_ids for asset_id in records)
    rows = []
    for asset in assets:
        amounts = records.get(asset["asset_id"], [])
        if len(amounts) == 1:
            row = {
                **asset,
                "amount_cents": amounts[0],
                "status": "reported",
                "reason": None,
            }
        elif len(amounts) > 1:
            row = {
                **asset,
                "amount_cents": None,
                "status": "unavailable",
                "reason": "Multiple values were recorded for this asset; no value is selected.",
            }
        else:
            row = {
                **asset,
                "amount_cents": None,
                "status": "unavailable",
                "reason": "No value is recorded for this asset.",
            }
        rows.append(row)
    return available, rows


def _scenario_values(
    assets: list[dict[str, str]],
    scenario_result: dict,
) -> tuple[bool, list[dict[str, Any]], list[dict[str, Any]], str | None]:
    scenario = scenario_result.get("scenario")
    share_bps = scenario.get("community_share_bps") if isinstance(scenario, dict) else None
    if _integer(share_bps) is None or not 0 <= share_bps <= 10_000:
        return False, [], [], None
    scenario_id = scenario.get("id")
    ledger_results = scenario_result.get("ledgers")
    if not isinstance(ledger_results, list):
        return False, [], [], str(scenario_id) if scenario_id else None
    result_by_id: dict[str, list[dict]] = {}
    for result in ledger_results:
        if isinstance(result, dict) and isinstance(result.get("asset_id"), str):
            result_by_id.setdefault(result["asset_id"], []).append(result)
    user_rows = []
    other_rows = []
    for asset in assets:
        matches = result_by_id.get(asset["asset_id"], [])
        if len(matches) != 1:
            reason = "The saved scenario does not have exactly one result for this asset."
            user_rows.append(_unavailable_scenario_value(asset, reason))
            other_rows.append(_unavailable_scenario_value(asset, reason))
            continue
        balances = matches[0].get("balances")
        if not isinstance(balances, dict):
            user_rows.append(_unavailable_scenario_value(asset, "The saved scenario has no per-asset balance."))
            other_rows.append(_unavailable_scenario_value(asset, "The saved scenario has no per-asset balance."))
            continue
        user_separate = _integer(balances.get("user_separate_cents"))
        other_separate = _integer(balances.get("other_separate_cents"))
        community = _integer(balances.get("community_cents"))
        unresolved = _integer(balances.get("unresolved_cents"))
        if None in (user_separate, other_separate, community, unresolved):
            reason = "The saved scenario has incomplete per-party balances."
            user_rows.append(_unavailable_scenario_value(asset, reason))
            other_rows.append(_unavailable_scenario_value(asset, reason))
            continue
        if asset["asset_kind"] not in {"asset", "debt"}:
            user_rows.append(_unavailable_scenario_value(asset, "The asset or debt type is not recorded."))
            other_rows.append(_unavailable_scenario_value(asset, "The asset or debt type is not recorded."))
            continue
        community_for_user = community * share_bps // 10_000
        user_amount = user_separate + community_for_user
        other_amount = other_separate + community - community_for_user
        if asset["asset_kind"] == "debt":
            user_amount *= -1
            other_amount *= -1
        user_rows.append(_calculated_scenario_value(asset, user_amount, unresolved))
        other_rows.append(_calculated_scenario_value(asset, other_amount, unresolved))
    return (
        any(row["amount_cents"] is not None for row in user_rows),
        user_rows,
        other_rows,
        str(scenario_id) if scenario_id else None,
    )


def _unavailable_scenario_value(asset: dict[str, str], reason: str) -> dict[str, Any]:
    return {
        **asset,
        "amount_cents": None,
        "unresolved_cents": None,
        "status": "unavailable",
        "reason": reason,
    }


def _calculated_scenario_value(
    asset: dict[str, str],
    amount: int,
    unresolved: int,
) -> dict[str, Any]:
    return {
        **asset,
        "amount_cents": amount,
        "unresolved_cents": unresolved,
        "status": "partial_unresolved" if unresolved else "calculated",
        "reason": (
            "Unresolved value is excluded from this party allocation."
            if unresolved
            else None
        ),
    }


def _series(
    series_id: str,
    label: str,
    available: bool,
    values: list[dict[str, Any]],
    *,
    source: str,
    reason: str | None = None,
    attempt_ordinal: int,
    proposal_version_ordinal: int | None = None,
    recorded_at: str | None = None,
    verified_by_app: bool | None = None,
    scenario_id: str | None = None,
) -> dict[str, Any]:
    result = {
        "id": series_id,
        "label": label,
        "available": available,
        "values": values,
        "source": source,
        "reason": reason if not available else None,
        "attempt_ordinal": attempt_ordinal,
        "proposal_version_ordinal": proposal_version_ordinal,
    }
    if recorded_at is not None:
        result["recorded_at"] = recorded_at
    if verified_by_app is not None:
        result["verified_by_app"] = verified_by_app
    if scenario_id is not None:
        result["scenario_id"] = scenario_id
    return result


def _summary(assets: list[dict[str, str]], values: list[dict[str, Any]]) -> dict[str, Any]:
    by_id = {value["asset_id"]: value for value in values}
    known_values = [
        value["amount_cents"]
        for value in by_id.values()
        if _integer(value.get("amount_cents")) is not None
    ]
    unresolved_count = sum(
        value.get("status") == "partial_unresolved" for value in by_id.values()
    )
    missing_count = sum(
        _integer(by_id.get(asset["asset_id"], {}).get("amount_cents")) is None
        for asset in assets
    )
    complete = bool(assets) and missing_count == 0 and unresolved_count == 0
    has_known = bool(known_values)
    return {
        "amount_cents": sum(known_values) if complete else None,
        "known_subtotal_cents": sum(known_values) if has_known else None,
        "status": "complete" if complete else ("partial" if has_known else "unavailable"),
        "missing_asset_count": missing_count,
        "unresolved_asset_count": unresolved_count,
    }


def _difference(
    assets: list[dict[str, str]],
    series_by_id: dict[str, dict[str, Any]],
    difference_id: str,
    label: str,
    minuend_id: str,
    subtrahend_id: str,
) -> dict[str, Any]:
    minuend = series_by_id[minuend_id]
    subtrahend = series_by_id[subtrahend_id]
    minuend_values = {item["asset_id"]: item for item in minuend["values"]}
    subtrahend_values = {item["asset_id"]: item for item in subtrahend["values"]}
    rows = []
    for asset in assets:
        left = minuend_values.get(asset["asset_id"])
        right = subtrahend_values.get(asset["asset_id"])
        left_amount = _integer(left.get("amount_cents")) if left else None
        right_amount = _integer(right.get("amount_cents")) if right else None
        if (
            left_amount is not None
            and right_amount is not None
            and left.get("status") != "partial_unresolved"
            and right.get("status") != "partial_unresolved"
        ):
            rows.append(
                {
                    **asset,
                    "amount_cents": left_amount - right_amount,
                    "status": "calculated",
                    "reason": None,
                }
            )
        else:
            rows.append(
                {
                    **asset,
                    "amount_cents": None,
                    "status": "unavailable",
                    "reason": "A complete value for both compared series is unavailable.",
                }
            )
    summary = _summary(assets, rows)
    return {
        "id": difference_id,
        "label": label,
        "minuend": minuend_id,
        "subtrahend": subtrahend_id,
        "values": rows,
        **summary,
    }


def _counteroffer_context(
    record: dict | None,
    attempt_ordinal: int,
    proposal_version_ordinal: int | None,
    relationship: str,
) -> dict[str, Any]:
    if not isinstance(record, dict):
        return {
            "available": False,
            "attempt_ordinal": attempt_ordinal,
            "proposal_version_ordinal": proposal_version_ordinal,
            "relationship": relationship,
            "source": None,
            "note": None,
            "recorded_at": None,
            "verified_by_app": False,
        }
    return {
        "available": True,
        "attempt_ordinal": attempt_ordinal,
        "proposal_version_ordinal": proposal_version_ordinal,
        "relationship": relationship,
        "source": record.get("source"),
        "note": record.get("note"),
        "recorded_at": record.get("recorded_at"),
        "verified_by_app": False,
    }


def build_offer_comparison(
    *,
    attempt_ordinal: int,
    proposal_version_ordinal: int,
    finalized: bool,
    offer_origin: str,
    snapshot: dict,
    scenario_result: dict,
    editable_state: dict,
    prior_attempt: dict | None,
    current_counteroffer: dict | None,
) -> dict[str, Any]:
    """Build read-only comparison data from the saved attempt and offer records."""
    assets = _asset_rows(snapshot)
    user_values, current_proposal_rows = _recorded_values(
        assets,
        editable_state.get("proposed_values"),
        value_key="proposed_amount_cents",
    )
    prior_attempt = prior_attempt if isinstance(prior_attempt, dict) else None
    prior_proposal = prior_attempt.get("user_proposed_values", []) if prior_attempt else []
    prior_ordinal = prior_attempt.get("attempt_ordinal") if prior_attempt else attempt_ordinal
    prior_version = prior_attempt.get("proposal_version_ordinal") if prior_attempt else None
    prior_values, prior_proposal_rows = _recorded_values(
        assets,
        prior_proposal,
        value_key="proposed_amount_cents",
    )
    prior_counteroffer = prior_attempt.get("counteroffer") if prior_attempt else None
    has_prior_counteroffer = isinstance(prior_counteroffer, dict)
    has_current_counteroffer = isinstance(current_counteroffer, dict)
    incoming_counteroffer = (
        prior_counteroffer if has_prior_counteroffer else current_counteroffer
    )
    counteroffer_ordinal = prior_ordinal if has_prior_counteroffer else attempt_ordinal
    counteroffer_relationship = (
        "preceded_this_attempt" if has_prior_counteroffer else "current_attempt_response"
    )
    counteroffer_values = (
        incoming_counteroffer.get("values", [])
        if isinstance(incoming_counteroffer, dict)
        else []
    )
    counteroffer_rows_available, counteroffer_rows = _recorded_values(
        assets,
        counteroffer_values,
        value_key="amount_cents",
    )
    counteroffer_available = (
        isinstance(incoming_counteroffer, dict) and counteroffer_rows_available
    )
    if not counteroffer_available:
        counteroffer_rows = []
    current_response_values, current_response_rows = _recorded_values(
        assets,
        current_counteroffer.get("values", []) if has_current_counteroffer else [],
        value_key="amount_cents",
    )
    current_response_available = (
        has_prior_counteroffer and has_current_counteroffer and current_response_values
    )
    if not current_response_available:
        current_response_rows = []
    projected_rows = [
        {
            **row,
            "status": "reported_projection" if row["amount_cents"] is not None else row["status"],
            "reason": (
                "Uses the reported counteroffer amount; acceptance is not recorded or predicted."
                if row["amount_cents"] is not None
                else row["reason"]
            ),
        }
        for row in counteroffer_rows
    ]
    scenario_available, party_rows, other_rows, scenario_id = _scenario_values(
        assets, scenario_result
    )
    case_metadata = (snapshot.get("case_profile") or {}).get("metadata") or {}
    incoming_offer = case_metadata.get("existing_offer")
    incoming_offer = incoming_offer if isinstance(incoming_offer, dict) else {}
    series = [
        _series(
            "party_baseline",
            "Your baseline",
            False,
            [],
            source="unavailable",
            reason=_BASELINE_UNAVAILABLE,
            attempt_ordinal=attempt_ordinal,
        ),
        _series(
            "party_value",
            "Your current scenario value",
            scenario_available,
            party_rows,
            source="saved_attempt_scenario",
            reason=None if scenario_available else _SCENARIO_UNAVAILABLE,
            attempt_ordinal=attempt_ordinal,
            proposal_version_ordinal=proposal_version_ordinal,
            scenario_id=scenario_id,
        ),
        _series(
            "opposing_baseline",
            "Other party baseline",
            False,
            [],
            source="unavailable",
            reason=_BASELINE_UNAVAILABLE,
            attempt_ordinal=attempt_ordinal,
        ),
        _series(
            "opposing_value",
            "Other party current scenario value",
            scenario_available,
            other_rows,
            source="saved_attempt_scenario",
            reason=None if scenario_available else _SCENARIO_UNAVAILABLE,
            attempt_ordinal=attempt_ordinal,
            proposal_version_ordinal=proposal_version_ordinal,
            scenario_id=scenario_id,
        ),
        _series(
            "prior_proposal",
            "Your prior proposal",
            prior_values,
            prior_proposal_rows,
            source="immutable_predecessor_attempt",
            reason="No prior user proposal is recorded for this attempt.",
            attempt_ordinal=prior_ordinal,
            proposal_version_ordinal=prior_version,
        ),
        _series(
            "counteroffer",
            (
                "Counteroffer that preceded this attempt"
                if has_prior_counteroffer
                else "Recorded counteroffer response"
            ),
            counteroffer_available,
            counteroffer_rows,
            source=(
                str(incoming_counteroffer.get("source") or "recorded_counteroffer")
                if isinstance(incoming_counteroffer, dict)
                else "unavailable"
            ),
            reason="No structured counteroffer amounts are recorded for this attempt.",
            attempt_ordinal=counteroffer_ordinal,
            recorded_at=(
                incoming_counteroffer.get("recorded_at")
                if isinstance(incoming_counteroffer, dict)
                and isinstance(incoming_counteroffer.get("recorded_at"), str)
                else None
            ),
            verified_by_app=False,
            proposal_version_ordinal=(
                prior_version if has_prior_counteroffer else proposal_version_ordinal
            ),
        ),
        _series(
            "current_response_counteroffer",
            "Current attempt's newly reported counteroffer",
            current_response_available,
            current_response_rows,
            source=(
                str(current_counteroffer.get("source") or "recorded_counteroffer")
                if has_current_counteroffer
                else "unavailable"
            ),
            reason="No separate current-attempt counteroffer amounts are recorded.",
            attempt_ordinal=attempt_ordinal,
            recorded_at=(
                current_counteroffer.get("recorded_at")
                if has_current_counteroffer
                and isinstance(current_counteroffer.get("recorded_at"), str)
                else None
            ),
            verified_by_app=False,
            proposal_version_ordinal=proposal_version_ordinal,
        ),
        _series(
            "projected_if_accepted",
            "Your projected allocation if counteroffer accepted",
            counteroffer_available,
            projected_rows,
            source="reported_counteroffer_values",
            reason="No recorded counteroffer amounts are available to project.",
            attempt_ordinal=counteroffer_ordinal,
            recorded_at=(
                incoming_counteroffer.get("recorded_at")
                if isinstance(incoming_counteroffer, dict)
                and isinstance(incoming_counteroffer.get("recorded_at"), str)
                else None
            ),
            verified_by_app=False,
            proposal_version_ordinal=(
                prior_version if has_prior_counteroffer else proposal_version_ordinal
            ),
        ),
        _series(
            "current_proposal",
            "Your current editable proposal",
            user_values,
            current_proposal_rows,
            source="user_editable_attempt_state",
            reason="No current proposal amounts are recorded for this attempt.",
            attempt_ordinal=attempt_ordinal,
            proposal_version_ordinal=proposal_version_ordinal,
        ),
    ]
    series_by_id = {item["id"]: item for item in series}
    differences = [
        _difference(
            assets,
            series_by_id,
            "party_vs_opposing_value",
            "Your scenario value minus other party scenario value",
            "party_value",
            "opposing_value",
        ),
        _difference(
            assets,
            series_by_id,
            "current_vs_prior_proposal",
            "Current proposal minus your prior proposal",
            "current_proposal",
            "prior_proposal",
        ),
        _difference(
            assets,
            series_by_id,
            "current_vs_counteroffer",
            "Current proposal minus counteroffer that preceded this attempt",
            "current_proposal",
            "counteroffer",
        ),
        _difference(
            assets,
            series_by_id,
            "current_vs_latest_response_counteroffer",
            "Current proposal minus current attempt's newly reported counteroffer",
            "current_proposal",
            "current_response_counteroffer",
        ),
    ]
    return {
        "attempt": {
            "ordinal": attempt_ordinal,
            "proposal_version_ordinal": proposal_version_ordinal,
            "finalized": finalized,
        },
        "offer_origin": offer_origin,
        "initial_incoming_offer": {
            "available": offer_origin == "initial_incoming_offer",
            "notes": incoming_offer.get("notes"),
            "asset_terms": deepcopy(incoming_offer.get("asset_terms", [])),
            "source": "case_intake",
            "recorded_at": incoming_offer.get("updated_at"),
            "reason": (
                "The incoming offer is recorded as notes or terms, not as verified asset amounts."
                if offer_origin == "initial_incoming_offer"
                else None
            ),
        },
        "counteroffer_context": _counteroffer_context(
            incoming_counteroffer,
            counteroffer_ordinal,
            prior_version if has_prior_counteroffer else proposal_version_ordinal,
            counteroffer_relationship,
        ),
        "current_response_counteroffer_context": (
            _counteroffer_context(
                current_counteroffer,
                attempt_ordinal,
                proposal_version_ordinal,
                "current_attempt_response",
            )
            if has_current_counteroffer and has_prior_counteroffer
            else None
        ),
        "assets": assets,
        "series": series,
        "totals": {
            item["id"]: _summary(assets, item["values"])
            for item in series
        },
        "differences": differences,
    }
