"""Deterministic timeline construction for bars, orders, and corporate actions."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from tradeguard.backtest.models import BacktestPlan, PlannedOrder
from tradeguard.data.models import MARKET_RECORD_ADAPTER, CorporateAction, OHLCVBar
from tradeguard.data.package import DatasetPackage
from tradeguard.domain.serialization import UtcDateTime, deterministic_checksum


class TimelineKind(IntEnum):
    CORPORATE_ACTION = 0
    ORDER = 1
    BAR = 2


@dataclass(frozen=True)
class TimelineEvent:
    event_time_utc: UtcDateTime
    ingest_time_utc: UtcDateTime
    sequence_number: int
    kind: TimelineKind
    tie_breaker: str
    payload: CorporateAction | PlannedOrder | OHLCVBar

    @property
    def ordering_key(self) -> tuple[object, ...]:
        return (
            self.event_time_utc,
            self.ingest_time_utc,
            self.sequence_number,
            int(self.kind),
            self.tie_breaker,
        )


def build_timeline(
    package: DatasetPackage,
    plan: BacktestPlan,
) -> tuple[tuple[TimelineEvent, ...], int]:
    """Return stable total ordering and the number of ignored non-bar records."""

    events: list[TimelineEvent] = []
    ignored_records = 0
    for document in package.records:
        record = MARKET_RECORD_ADAPTER.validate_python(document)
        if not isinstance(record, OHLCVBar):
            ignored_records += 1
            continue
        events.append(
            TimelineEvent(
                event_time_utc=record.event_time_utc,
                ingest_time_utc=record.ingest_time_utc,
                sequence_number=record.sequence_number,
                kind=TimelineKind.BAR,
                tie_breaker=deterministic_checksum(record),
                payload=record,
            )
        )
    events.extend(
        TimelineEvent(
            event_time_utc=order.submitted_at_utc,
            ingest_time_utc=order.submitted_at_utc,
            sequence_number=order.sequence_number,
            kind=TimelineKind.ORDER,
            tie_breaker=deterministic_checksum(order),
            payload=order,
        )
        for order in plan.orders
    )
    for action in package.corporate_actions:
        if action.known_at > package.policy.knowledge_time_utc:
            continue
        events.append(
            TimelineEvent(
                event_time_utc=action.effective_at,
                ingest_time_utc=max(action.effective_at, action.known_at),
                sequence_number=0,
                kind=TimelineKind.CORPORATE_ACTION,
                tie_breaker=deterministic_checksum(action),
                payload=action,
            )
        )
    return tuple(sorted(events, key=lambda event: event.ordering_key)), ignored_records
