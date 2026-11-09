"""Validated, explicitly entered dated balances for the case overview."""

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

OVERVIEW_CATEGORIES = frozenset({
    "Home equity", "Retirement accounts", "Cash and savings", "Vehicles", "Debt",
})

class OverviewBalance(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: str = Field(min_length=1, max_length=120, pattern=r"\S")
    you_cents: int | None = Field(default=None, ge=-10**14, le=10**14, strict=True)
    other_cents: int | None = Field(default=None, ge=-10**14, le=10**14, strict=True)


class OverviewSnapshot(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    balances: list[OverviewBalance] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def unique_categories(self) -> "OverviewSnapshot":
        if len({item.category for item in self.balances}) != len(self.balances):
            raise ValueError("Balance categories must be unique within a dated snapshot.")
        you = sum(item.you_cents or 0 for item in self.balances)
        other = sum(item.other_cents or 0 for item in self.balances)
        if any(abs(total) > 9_007_199_254_740_991 for total in (you, other, you + other)):
            raise ValueError("Snapshot totals exceed the supported exact-integer range.")
        return self


class OverviewMilestone(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(min_length=1, max_length=80, pattern=r"\S")
    date: date


class AssetOverview(BaseModel):
    model_config = ConfigDict(extra="forbid")

    snapshots: list[OverviewSnapshot] = Field(default_factory=list, max_length=200)
    milestones: list[OverviewMilestone] = Field(default_factory=list, max_length=100)

    @model_validator(mode="after")
    def unique_dates(self) -> "AssetOverview":
        if len({item.date for item in self.snapshots}) != len(self.snapshots):
            raise ValueError("Snapshot dates must be unique.")
        return self


class AssetOverviewUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0, strict=True)
    overview: AssetOverview


class AssetOverviewRead(BaseModel):
    revision: int = Field(default=0, ge=0)
    overview: AssetOverview = Field(default_factory=AssetOverview)


class OverviewScenarioExport(BaseModel):
    model_config = ConfigDict(extra="forbid")

    expected_revision: int = Field(ge=0, strict=True)
    attempt_ordinal: int = Field(ge=1, strict=True)
    start_date: date
    end_date: date
    community_share_bps: Literal[4500, 5000, 5500]

    @model_validator(mode="after")
    def ordered_dates(self) -> "OverviewScenarioExport":
        if self.start_date > self.end_date:
            raise ValueError("Start date must not follow the division date.")
        return self

    def snapshots(self, overview: AssetOverview) -> tuple[OverviewSnapshot, OverviewSnapshot]:
        dates = {snapshot.date: snapshot for snapshot in overview.snapshots}
        start, end = dates.get(self.start_date), dates.get(self.end_date)
        if start is None or end is None:
            raise ValueError("Both dates must have saved balances.")
        for snapshot in (start, end):
            if not OVERVIEW_CATEGORIES.issubset({balance.category for balance in snapshot.balances}) or any(
                balance.you_cents is None or balance.other_cents is None
                for balance in snapshot.balances
            ):
                raise ValueError("Both dates require complete balances. Missing values are not zero.")
        return start, end
