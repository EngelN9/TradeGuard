"""Fail-closed bar execution without ideal fills or same-close look-ahead."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal
from enum import StrEnum

from tradeguard.backtest.models import PlannedOrder
from tradeguard.costs.models import CostBreakdown, CryptoCostModel, EquityCostModel
from tradeguard.data.models import (
    InstrumentMetadata,
    MaintenanceInterval,
    MarketSession,
    OHLCVBar,
    SessionStatus,
)
from tradeguard.domain.events import AssetClass, OrderType, Side
from tradeguard.domain.serialization import AuthorityDecimal, UtcDateTime


class ExecutionDisposition(StrEnum):
    FILL = "fill"
    WAIT = "wait"
    BLOCK = "block"
    REJECT = "reject"


@dataclass(frozen=True)
class ExecutionDecision:
    disposition: ExecutionDisposition
    reason: str
    quantity: Decimal = Decimal("0")
    price: Decimal = Decimal("0")
    costs: CostBreakdown | None = None


class ConservativeBarExecutionModel:
    """Execute only after an order is knowable and against a future bar."""

    def evaluate(  # noqa: PLR0911, PLR0913 - fail-closed inputs remain explicit
        self,
        *,
        order: PlannedOrder,
        remaining_quantity: AuthorityDecimal,
        bar: OHLCVBar,
        metadata: InstrumentMetadata,
        knowledge_time_utc: UtcDateTime,
        latency_seconds: int,
        max_participation_rate: AuthorityDecimal,
        consumed_participation_quantity: AuthorityDecimal = Decimal("0"),
        equity_costs: EquityCostModel,
        crypto_costs: CryptoCostModel,
        market_sessions: tuple[MarketSession, ...],
        maintenance_intervals: tuple[MaintenanceInterval, ...],
    ) -> ExecutionDecision:
        if (order.asset_class, order.venue, order.symbol) != (
            bar.asset_class,
            bar.venue,
            bar.symbol,
        ):
            return ExecutionDecision(ExecutionDisposition.WAIT, "different_instrument")
        if not metadata.is_point_in_time_valid(
            effective_at=bar.event_time_utc,
            knowledge_time=knowledge_time_utc,
        ):
            return ExecutionDecision(ExecutionDisposition.REJECT, "metadata_unknown_or_inactive")
        if order.quantity < metadata.minimum_quantity:
            return ExecutionDecision(ExecutionDisposition.REJECT, "minimum_quantity_rejected")
        if not self._valid_order_precision(order, metadata):
            return ExecutionDecision(ExecutionDisposition.REJECT, "order_precision_rejected")
        if bar.interval_start_utc < order.submitted_at_utc:
            return ExecutionDecision(ExecutionDisposition.WAIT, "look_ahead_guard_same_bar")
        eligible_at = order.submitted_at_utc + timedelta(seconds=latency_seconds)
        if bar.event_time_utc <= eligible_at:
            return ExecutionDecision(ExecutionDisposition.WAIT, "latency_not_elapsed")
        if order.asset_class is AssetClass.EQUITY and not self._equity_session_open(
            bar, market_sessions, knowledge_time_utc
        ):
            return ExecutionDecision(ExecutionDisposition.BLOCK, "equity_session_closed_or_unknown")
        if order.asset_class is AssetClass.CRYPTO and self._maintenance_overlaps(
            bar, maintenance_intervals, knowledge_time_utc
        ):
            return ExecutionDecision(ExecutionDisposition.BLOCK, "venue_maintenance")

        price = self._candidate_price(order, bar)
        if price is None:
            return ExecutionDecision(ExecutionDisposition.WAIT, "limit_not_crossed")
        if order.quantity * price < metadata.minimum_notional:
            return ExecutionDecision(ExecutionDisposition.REJECT, "minimum_notional_rejected")

        increment = (
            metadata.lot_size if order.asset_class is AssetClass.EQUITY else metadata.step_size
        )
        remaining_bar_capacity = max(
            bar.volume * max_participation_rate - consumed_participation_quantity,
            Decimal("0"),
        )
        available = self._floor_to_increment(remaining_bar_capacity, increment)
        fill_quantity = min(remaining_quantity, available)
        fill_quantity = self._floor_to_increment(fill_quantity, increment)
        if (
            fill_quantity < metadata.minimum_quantity
            or fill_quantity * price < metadata.minimum_notional
        ):
            return ExecutionDecision(ExecutionDisposition.WAIT, "insufficient_bar_liquidity")

        costs = (
            equity_costs.calculate(
                side=order.side,
                order_type=order.order_type,
                price=price,
                quantity=fill_quantity,
            )
            if order.asset_class is AssetClass.EQUITY
            else crypto_costs.calculate(
                side=order.side,
                order_type=order.order_type,
                price=price,
                quantity=fill_quantity,
            )
        )
        return ExecutionDecision(
            ExecutionDisposition.FILL,
            "conservative_future_bar_fill",
            quantity=fill_quantity,
            price=price,
            costs=costs,
        )

    @staticmethod
    def _valid_order_precision(order: PlannedOrder, metadata: InstrumentMetadata) -> bool:
        increment = (
            metadata.lot_size if order.asset_class is AssetClass.EQUITY else metadata.step_size
        )
        if order.quantity % increment != 0:
            return False
        return order.limit_price is None or order.limit_price % metadata.tick_size == 0

    @staticmethod
    def _candidate_price(order: PlannedOrder, bar: OHLCVBar) -> Decimal | None:
        if order.order_type is OrderType.MARKET:
            return bar.high_price if order.side is Side.BUY else bar.low_price
        if order.limit_price is None:
            return None
        crossed = (
            bar.low_price <= order.limit_price
            if order.side is Side.BUY
            else bar.high_price >= order.limit_price
        )
        return order.limit_price if crossed else None

    @staticmethod
    def _floor_to_increment(value: Decimal, increment: Decimal) -> Decimal:
        return (value // increment) * increment

    @staticmethod
    def _equity_session_open(
        bar: OHLCVBar,
        sessions: tuple[MarketSession, ...],
        knowledge_time_utc: UtcDateTime,
    ) -> bool:
        return any(
            session.venue == bar.venue
            and session.known_at <= knowledge_time_utc
            and session.status is SessionStatus.OPEN
            and session.contains(bar.interval_start_utc)
            for session in sessions
        )

    @staticmethod
    def _maintenance_overlaps(
        bar: OHLCVBar,
        intervals: tuple[MaintenanceInterval, ...],
        knowledge_time_utc: UtcDateTime,
    ) -> bool:
        return any(
            interval.venue == bar.venue
            and interval.known_at <= knowledge_time_utc
            and interval.start_utc < bar.interval_end_utc
            and interval.end_utc > bar.interval_start_utc
            for interval in intervals
        )
