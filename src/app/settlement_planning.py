import hashlib
import re
from collections.abc import Sequence
from datetime import date, datetime
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

SourceBucket = Literal[
    "user_separate",
    "other_separate",
    "community",
    "unresolved",
]
TraceMethod = Literal[
    "explicit",
    "pro_rata",
    "user_separate_first",
    "other_separate_first",
    "community_first",
    "unresolved_first",
]
LedgerEventType = Literal[
    "acquisition",
    "contribution",
    "income",
    "withdrawal",
    "expense",
    "debt_payment",
    "transfer_out",
    "transfer_in",
    "valuation",
]
MAX_AMOUNT_CENTS = 10**15
SOURCE_BUCKETS: tuple[SourceBucket, ...] = (
    "user_separate",
    "other_separate",
    "community",
    "unresolved",
)
CREDIT_EVENT_TYPES = {"acquisition", "contribution", "income", "transfer_in"}
DEBIT_EVENT_TYPES = {"withdrawal", "expense", "debt_payment", "transfer_out"}


class LedgerEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID = Field(default_factory=uuid4)
    effective_date: date
    sequence_number: int = Field(default=0, ge=0, strict=True)
    event_type: LedgerEventType
    amount_cents: int = Field(gt=0, le=MAX_AMOUNT_CENTS, strict=True)
    source_allocations: dict[SourceBucket, int] | None = None
    earned_by: Literal["user", "other"] | None = None
    transfer_id: UUID | None = None
    provenance: Literal[
        "source_supported",
        "user_reported",
        "scenario_assumed",
        "disputed",
        "unresolved",
    ]
    source_fact_ids: list[UUID] = Field(default_factory=list, max_length=50)
    note: str = Field(default="", max_length=1000)

    @model_validator(mode="before")
    @classmethod
    def dates_must_be_calendar_dates(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        raw_date = value.get("effective_date")
        if isinstance(raw_date, datetime):
            raise ValueError("Use an ISO calendar date in YYYY-MM-DD format.")
        if isinstance(raw_date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date) is None:
            raise ValueError("Use an ISO calendar date in YYYY-MM-DD format.")
        return value

    @model_validator(mode="after")
    def validate_event_sources(self) -> "LedgerEvent":
        if self.event_type == "valuation":
            if self.source_allocations is not None or self.earned_by is not None:
                raise ValueError("A valuation records total value, not a source allocation.")
            if self.transfer_id is not None:
                raise ValueError("A valuation cannot be a transfer.")
        elif self.source_allocations is not None:
            if sum(self.source_allocations.values()) != self.amount_cents:
                raise ValueError("Source allocations must add up to the event amount.")
        if self.event_type in {"transfer_in", "transfer_out"}:
            if self.transfer_id is None or self.source_allocations is None:
                raise ValueError("Transfers require a matching ID and explicit source allocations.")
        elif self.transfer_id is not None:
            raise ValueError("Only transfer events may have a transfer ID.")
        if self.event_type == "income" and self.source_allocations is None:
            if self.earned_by is None:
                raise ValueError("Unallocated income requires the earning party or an unresolved source.")
        elif self.earned_by is not None:
            raise ValueError("The earning party is only valid for unallocated income.")
        if self.provenance == "source_supported" and not self.source_fact_ids:
            raise ValueError("Source-supported events require at least one reviewed source fact.")
        if len(set(self.source_fact_ids)) != len(self.source_fact_ids):
            raise ValueError("Source fact IDs must be unique.")
        return self


class AssetLedger(BaseModel):
    model_config = ConfigDict(extra="forbid")

    asset_id: UUID
    name: str = Field(min_length=1, max_length=200)
    kind: Literal["asset", "debt"]
    events: list[LedgerEvent] = Field(min_length=1, max_length=1000)

    @model_validator(mode="after")
    def name_must_not_be_blank(self) -> "AssetLedger":
        if not self.name.strip():
            raise ValueError("Ledger name cannot be blank.")
        if len({event.id for event in self.events}) != len(self.events):
            raise ValueError("Ledger event IDs must be unique.")
        event_order = [
            (event.effective_date, event.sequence_number)
            for event in self.events
        ]
        if len(set(event_order)) != len(event_order):
            raise ValueError(
                "Events on the same date need distinct sequence numbers."
            )
        return self


class RelationshipWindow(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1, max_length=80, pattern=r"^[A-Za-z0-9_-]+$")
    label: str = Field(min_length=1, max_length=160)
    relationship_type: Literal["cir_assumed", "marriage_only", "alternate"]
    start_date: date
    separation_date: date
    source_fact_ids: list[UUID] = Field(default_factory=list, max_length=50)
    assumption_note: str = Field(default="", max_length=1000)

    @model_validator(mode="before")
    @classmethod
    def dates_must_be_calendar_dates(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value
        for field in ("start_date", "separation_date"):
            raw_date = value.get(field)
            if isinstance(raw_date, datetime):
                raise ValueError("Use ISO calendar dates in YYYY-MM-DD format.")
            if isinstance(raw_date, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw_date) is None:
                raise ValueError("Use ISO calendar dates in YYYY-MM-DD format.")
        return value

    @model_validator(mode="after")
    def validate_relationship_window(self) -> "RelationshipWindow":
        if not self.label.strip():
            raise ValueError("Scenario window label cannot be blank.")
        if self.start_date > self.separation_date:
            raise ValueError("Relationship start date must not follow the separation date.")
        if len(set(self.source_fact_ids)) != len(self.source_fact_ids):
            raise ValueError("Window source fact IDs must be unique.")
        return self


class ScenarioAxes(BaseModel):
    model_config = ConfigDict(extra="forbid")

    relationship_windows: list[RelationshipWindow] = Field(min_length=1, max_length=3)
    tracing_methods: list[TraceMethod] = Field(min_length=1, max_length=3)
    community_share_bps: list[int] = Field(min_length=1, max_length=3)

    @model_validator(mode="after")
    def validate_distinct_axes(self) -> "ScenarioAxes":
        if len({window.id for window in self.relationship_windows}) != len(
            self.relationship_windows
        ):
            raise ValueError("Relationship window IDs must be unique.")
        if len(set(self.tracing_methods)) != len(self.tracing_methods):
            raise ValueError("Tracing methods must be unique.")
        if len(set(self.community_share_bps)) != len(self.community_share_bps):
            raise ValueError("Community shares must be unique.")
        if any(not 0 <= share <= 10_000 for share in self.community_share_bps):
            raise ValueError("Community share must be between 0 and 10000 basis points.")
        return self


class SettlementScenario(BaseModel):
    id: str
    label: str
    relationship_window: RelationshipWindow
    tracing_method: TraceMethod
    community_share_bps: int


class TraceBalances(BaseModel):
    user_separate_cents: int
    other_separate_cents: int
    community_cents: int
    unresolved_cents: int

    @property
    def total_cents(self) -> int:
        return (
            self.user_separate_cents
            + self.other_separate_cents
            + self.community_cents
            + self.unresolved_cents
        )


class TraceStep(BaseModel):
    event_id: UUID
    effective_date: date
    event_type: LedgerEventType
    amount_cents: int
    applied_source_allocations: dict[SourceBucket, int]
    balances: TraceBalances


class LedgerTraceResult(BaseModel):
    asset_id: UUID
    name: str
    kind: Literal["asset", "debt"]
    balances: TraceBalances
    steps: list[TraceStep]


class SettlementScenarioResult(BaseModel):
    scenario: SettlementScenario
    ledgers: list[LedgerTraceResult]
    user_net_cents: int
    other_net_cents: int
    unresolved_cents: int


def _zero_balances() -> dict[SourceBucket, int]:
    return dict.fromkeys(SOURCE_BUCKETS, 0)


def _balance_model(balances: dict[SourceBucket, int]) -> TraceBalances:
    return TraceBalances(
        user_separate_cents=balances["user_separate"],
        other_separate_cents=balances["other_separate"],
        community_cents=balances["community"],
        unresolved_cents=balances["unresolved"],
    )


def _allocations_for_amount(
    amount: int,
    balances: dict[SourceBucket, int],
    method: TraceMethod,
) -> dict[SourceBucket, int]:
    if amount > sum(balances.values()):
        raise ValueError("Withdrawal exceeds the available ledger balance.")
    if method == "explicit":
        raise ValueError("This withdrawal needs explicit source allocations.")
    if method == "unresolved_first":
        order: Sequence[SourceBucket] = (
            "unresolved",
            "community",
            "user_separate",
            "other_separate",
        )
    elif method == "user_separate_first":
        order = ("user_separate", "community", "other_separate", "unresolved")
    elif method == "other_separate_first":
        order = ("other_separate", "community", "user_separate", "unresolved")
    elif method == "community_first":
        order = ("community", "user_separate", "other_separate", "unresolved")
    else:
        total = sum(balances.values())
        allocations = {
            bucket: amount * balances[bucket] // total
            for bucket in SOURCE_BUCKETS
        }
        remainder = amount - sum(allocations.values())
        for bucket in SOURCE_BUCKETS:
            if remainder == 0:
                break
            if balances[bucket] > allocations[bucket]:
                allocations[bucket] += 1
                remainder -= 1
        if remainder:
            raise ValueError("Withdrawal could not be allocated without exceeding a source balance.")
        return allocations

    remaining = amount
    allocations = _zero_balances()
    for bucket in order:
        allocation = min(remaining, balances[bucket])
        allocations[bucket] = allocation
        remaining -= allocation
    if remaining:
        raise ValueError("Withdrawal exceeds the available ledger balance.")
    return allocations


def _event_credit_allocations(
    event: LedgerEvent,
    window: RelationshipWindow | None,
) -> dict[SourceBucket, int]:
    if event.source_allocations is not None:
        return {bucket: event.source_allocations.get(bucket, 0) for bucket in SOURCE_BUCKETS}
    if event.event_type == "income" and event.earned_by is not None and window is not None:
        if window.start_date <= event.effective_date <= window.separation_date:
            return {
                "user_separate": 0,
                "other_separate": 0,
                "community": event.amount_cents,
                "unresolved": 0,
            }
        bucket: SourceBucket = (
            "user_separate" if event.earned_by == "user" else "other_separate"
        )
        return {
            source_bucket: event.amount_cents if source_bucket == bucket else 0
            for source_bucket in SOURCE_BUCKETS
        }
    return {
        "user_separate": 0,
        "other_separate": 0,
        "community": 0,
        "unresolved": event.amount_cents,
    }


def _valuation_balances(
    amount: int,
    balances: dict[SourceBucket, int],
) -> dict[SourceBucket, int]:
    current_total = sum(balances.values())
    if amount > MAX_AMOUNT_CENTS:
        raise ValueError("Valuation exceeds the supported monetary range.")
    if current_total == 0:
        return {
            "user_separate": 0,
            "other_separate": 0,
            "community": 0,
            "unresolved": amount,
        }
    new_balances = {
        bucket: amount * balances[bucket] // current_total
        for bucket in SOURCE_BUCKETS
    }
    remainder = amount - sum(new_balances.values())
    for bucket in SOURCE_BUCKETS:
        if remainder == 0:
            break
        if balances[bucket] > 0:
            new_balances[bucket] += 1
            remainder -= 1
    if remainder:
        raise ValueError("Valuation could not be allocated to the current source balances.")
    return new_balances


def _transfer_pairs(ledgers: list[AssetLedger]) -> None:
    transfers: dict[UUID, list[tuple[UUID, LedgerEvent]]] = {}
    event_ids: set[UUID] = set()
    for ledger in ledgers:
        for event in ledger.events:
            if event.id in event_ids:
                raise ValueError("Ledger event IDs must be unique across the case.")
            event_ids.add(event.id)
            if event.transfer_id is not None:
                transfers.setdefault(event.transfer_id, []).append((ledger.asset_id, event))
    for pair in transfers.values():
        if len(pair) != 2:
            raise ValueError("Each transfer requires exactly one matching outflow and inflow.")
        (out_asset_id, out_event), (in_asset_id, in_event) = sorted(
            pair,
            key=lambda item: (item[1].event_type != "transfer_out", item[0].hex),
        )
        if (
            out_event.event_type != "transfer_out"
            or in_event.event_type != "transfer_in"
            or out_asset_id == in_asset_id
            or out_event.amount_cents != in_event.amount_cents
            or out_event.source_allocations != in_event.source_allocations
            or out_event.effective_date > in_event.effective_date
        ):
            raise ValueError("A transfer requires matching source allocations and ordered outflow/inflow.")


def trace_ledgers(
    ledgers: list[AssetLedger],
    method: TraceMethod,
    window: RelationshipWindow | None = None,
) -> list[LedgerTraceResult]:
    _transfer_pairs(ledgers)
    results = []
    for ledger in ledgers:
        balances = _zero_balances()
        steps = []
        events = sorted(
            ledger.events,
            key=lambda event: (
                event.effective_date,
                event.sequence_number,
            ),
        )
        for event in events:
            applied = _zero_balances()
            if event.event_type == "valuation":
                balances = _valuation_balances(event.amount_cents, balances)
            elif event.event_type in CREDIT_EVENT_TYPES:
                applied = _event_credit_allocations(event, window)
                balances = {
                    bucket: balances[bucket] + applied[bucket]
                    for bucket in SOURCE_BUCKETS
                }
            elif event.event_type in DEBIT_EVENT_TYPES:
                if event.source_allocations is not None:
                    applied = {
                        bucket: event.source_allocations.get(bucket, 0)
                        for bucket in SOURCE_BUCKETS
                    }
                else:
                    applied = _allocations_for_amount(event.amount_cents, balances, method)
                for bucket in SOURCE_BUCKETS:
                    if applied[bucket] > balances[bucket]:
                        raise ValueError(
                            f"Withdrawal exceeds the available {bucket} source balance."
                        )
                balances = {
                    bucket: balances[bucket] - applied[bucket]
                    for bucket in SOURCE_BUCKETS
                }
            if sum(balances.values()) > MAX_AMOUNT_CENTS:
                raise ValueError("Ledger balance exceeds the supported monetary range.")
            steps.append(
                TraceStep(
                    event_id=event.id,
                    effective_date=event.effective_date,
                    event_type=event.event_type,
                    amount_cents=event.amount_cents,
                    applied_source_allocations=applied,
                    balances=_balance_model(balances),
                )
            )
        results.append(
            LedgerTraceResult(
                asset_id=ledger.asset_id,
                name=ledger.name,
                kind=ledger.kind,
                balances=_balance_model(balances),
                steps=steps,
            )
        )
    return results


def _scenario_label(
    window: RelationshipWindow,
    method: TraceMethod,
    community_share_bps: int,
) -> str:
    share = f"{community_share_bps // 100}.{community_share_bps % 100:02d}%"
    return f"{window.label} · {method.replace('_', ' ')} · {share} proposed community share"


def generate_scenarios(axes: ScenarioAxes, limit: int = 12) -> list[SettlementScenario]:
    if not 1 <= limit <= 12:
        raise ValueError("Scenario limit must be between 1 and 12.")
    axis_values = [
        axes.relationship_windows,
        axes.tracing_methods,
        axes.community_share_bps,
    ]
    indexes = [0, 0, 0]
    combinations = [tuple(indexes)]
    for axis_index, values in enumerate(axis_values):
        for value_index in range(1, len(values)):
            candidate = [0, 0, 0]
            candidate[axis_index] = value_index
            combinations.append(tuple(candidate))
    diagonal_count = max(len(values) for values in axis_values)
    for offset in range(1, diagonal_count):
        candidate = tuple(
            offset % len(values)
            for values in axis_values
        )
        if candidate not in combinations:
            combinations.append(candidate)

    scenarios = []
    seen = set()
    for indexes in combinations:
        window = axes.relationship_windows[indexes[0]]
        method = axes.tracing_methods[indexes[1]]
        share = axes.community_share_bps[indexes[2]]
        identity = f"{window.id}|{method}|{share}"
        if identity in seen:
            continue
        seen.add(identity)
        scenario_id = hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]
        scenarios.append(
            SettlementScenario(
                id=scenario_id,
                label=_scenario_label(window, method, share),
                relationship_window=window,
                tracing_method=method,
                community_share_bps=share,
            )
        )
        if len(scenarios) >= limit:
            break
    return scenarios


def calculate_scenario(
    scenario: SettlementScenario,
    ledgers: list[AssetLedger],
) -> SettlementScenarioResult:
    ledger_results = trace_ledgers(
        ledgers,
        scenario.tracing_method,
        scenario.relationship_window,
    )
    user_net = 0
    other_net = 0
    unresolved_net = 0
    for ledger in ledger_results:
        multiplier = 1 if ledger.kind == "asset" else -1
        community_for_user = (
            ledger.balances.community_cents * scenario.community_share_bps // 10_000
        )
        community_for_other = ledger.balances.community_cents - community_for_user
        user_net += multiplier * (ledger.balances.user_separate_cents + community_for_user)
        other_net += multiplier * (ledger.balances.other_separate_cents + community_for_other)
        unresolved_net += multiplier * ledger.balances.unresolved_cents
    return SettlementScenarioResult(
        scenario=scenario,
        ledgers=ledger_results,
        user_net_cents=user_net,
        other_net_cents=other_net,
        unresolved_cents=unresolved_net,
    )
