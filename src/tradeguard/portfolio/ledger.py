"""Cash-only, long-only Decimal ledger with idempotent fill application."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

from tradeguard.backtest.models import (
    ConservationReport,
    CorporateActionLedgerEntry,
    FillLedgerEntry,
    PnLLedgerEntry,
    PositionLedgerEntry,
)
from tradeguard.data.models import CorporateAction, CorporateActionType, SupportedAssetClass
from tradeguard.domain.events import Side
from tradeguard.domain.serialization import UtcDateTime, deterministic_checksum


class LedgerError(ValueError):
    """Base class for a fail-closed accounting rejection."""


class InsufficientCashError(LedgerError):
    """Raised when a simulated buy would create negative cash."""


class InsufficientPositionError(LedgerError):
    """Raised when a simulated sell would create a short position."""


@dataclass
class _Position:
    asset_class: SupportedAssetClass
    venue: str
    symbol: str
    quantity: Decimal = Decimal("0")
    average_cost: Decimal = Decimal("0")


class PortfolioLedger:
    """Authority ledger; no account, broker, or external side effects exist."""

    def __init__(self, *, initial_cash: Decimal, base_currency: str) -> None:
        if initial_cash <= 0:
            raise ValueError("initial_cash must be positive")
        if not base_currency:
            raise ValueError("base_currency must not be empty")
        self.initial_cash = initial_cash
        self.base_currency = base_currency
        self.cash = initial_cash
        self.realized_pnl = Decimal("0")
        self._positions: dict[tuple[str, str], _Position] = {}
        self._expected_quantities: dict[tuple[str, str], Decimal] = {}
        self._seen_fill_ids: set[str] = set()
        self._seen_action_ids: set[str] = set()
        self.duplicate_fill_ids_ignored = 0

    def apply_fill(self, fill: FillLedgerEntry) -> bool:
        """Apply one fill exactly once; reject cash or position underflow."""

        if fill.fill_id in self._seen_fill_ids:
            self.duplicate_fill_ids_ignored += 1
            return False
        notional = fill.notional
        key = (fill.venue, fill.symbol)
        position = self._positions.get(key)
        if fill.side is Side.BUY:
            cash_debit = notional + fill.costs.total
            if cash_debit > self.cash:
                raise InsufficientCashError("fill rejected: insufficient simulated cash")
            if position is None:
                position = _Position(
                    asset_class=fill.asset_class,
                    venue=fill.venue,
                    symbol=fill.symbol,
                )
                self._positions[key] = position
            prior_cost_basis = position.average_cost * position.quantity
            position.quantity += fill.quantity
            position.average_cost = (
                prior_cost_basis + notional + fill.costs.total
            ) / position.quantity
            self.cash -= cash_debit
            quantity_delta = fill.quantity
        else:
            if position is None or fill.quantity > position.quantity:
                raise InsufficientPositionError("fill rejected: insufficient simulated position")
            proceeds_after_costs = notional - fill.costs.total
            self.cash += proceeds_after_costs
            self.realized_pnl += proceeds_after_costs - position.average_cost * fill.quantity
            position.quantity -= fill.quantity
            if position.quantity == 0:
                position.average_cost = Decimal("0")
            quantity_delta = -fill.quantity
        self._expected_quantities[key] = (
            self._expected_quantities.get(key, Decimal("0")) + quantity_delta
        )
        self._seen_fill_ids.add(fill.fill_id)
        return True

    def apply_corporate_action(self, action: CorporateAction) -> CorporateActionLedgerEntry | None:
        """Apply a point-in-time equity action without rewriting market data."""

        action_checksum = deterministic_checksum(action)
        if action_checksum in self._seen_action_ids:
            return None
        key = (action.venue, action.symbol)
        position = self._positions.get(key)
        quantity_before = position.quantity if position is not None else Decimal("0")
        quantity_after = quantity_before
        symbol_after = action.symbol
        cash_delta = Decimal("0")

        if action.action_type in {CorporateActionType.SPLIT, CorporateActionType.REVERSE_SPLIT}:
            if action.ratio is None or action.ratio <= 0:
                raise LedgerError("split action requires a positive ratio")
            if position is not None:
                position.quantity *= action.ratio
                position.average_cost /= action.ratio
                quantity_after = position.quantity
                self._expected_quantities[key] = (
                    self._expected_quantities.get(key, Decimal("0")) * action.ratio
                )
        elif action.action_type is CorporateActionType.CASH_DIVIDEND:
            if action.cash_amount is None or action.cash_amount < 0:
                raise LedgerError("cash dividend requires a non-negative amount")
            if action.currency != self.base_currency:
                raise LedgerError("cash dividend currency differs from the base currency")
            cash_delta = quantity_before * action.cash_amount
            self.cash += cash_delta
            self.realized_pnl += cash_delta
        elif action.action_type is CorporateActionType.SYMBOL_CHANGE:
            if not action.new_symbol:
                raise LedgerError("symbol change requires new_symbol")
            symbol_after = action.new_symbol
            if position is not None:
                new_key = (action.venue, symbol_after)
                if new_key in self._positions:
                    raise LedgerError("symbol change target already has a position")
                position.symbol = symbol_after
                self._positions[new_key] = self._positions.pop(key)
                self._expected_quantities[new_key] = self._expected_quantities.pop(
                    key, Decimal("0")
                )
        elif action.action_type is not CorporateActionType.DELISTING:
            raise LedgerError("unsupported corporate action")

        self._seen_action_ids.add(action_checksum)
        return CorporateActionLedgerEntry(
            action_checksum=action_checksum,
            symbol_before=action.symbol,
            symbol_after=symbol_after,
            action_type=action.action_type.value,
            effective_at=action.effective_at,
            quantity_before=quantity_before,
            quantity_after=quantity_after,
            cash_delta=cash_delta,
        )

    def mark(
        self,
        *,
        event_time_utc: UtcDateTime,
        marks: dict[tuple[str, str], Decimal],
    ) -> tuple[tuple[PositionLedgerEntry, ...], PnLLedgerEntry]:
        """Create immutable position and PnL snapshots at reviewed marks."""

        snapshots: list[PositionLedgerEntry] = []
        market_value = Decimal("0")
        unrealized_pnl = Decimal("0")
        for key in sorted(self._positions):
            position = self._positions[key]
            mark_price = marks.get(key, Decimal("0"))
            value = position.quantity * mark_price
            unrealized = (mark_price - position.average_cost) * position.quantity
            market_value += value
            unrealized_pnl += unrealized
            snapshots.append(
                PositionLedgerEntry(
                    event_time_utc=event_time_utc,
                    asset_class=position.asset_class,
                    venue=position.venue,
                    symbol=position.symbol,
                    quantity=position.quantity,
                    average_cost=position.average_cost,
                    mark_price=mark_price,
                    market_value=value,
                    unrealized_pnl=unrealized,
                )
            )
        total_pnl = self.realized_pnl + unrealized_pnl
        pnl = PnLLedgerEntry(
            event_time_utc=event_time_utc,
            cash=self.cash,
            market_value=market_value,
            realized_pnl=self.realized_pnl,
            unrealized_pnl=unrealized_pnl,
            total_pnl=total_pnl,
            total_equity=self.cash + market_value,
        )
        return tuple(snapshots), pnl

    def conservation_report(self, pnl: PnLLedgerEntry) -> ConservationReport:
        differences = {}
        for (venue, symbol), expected in sorted(self._expected_quantities.items()):
            position = self._positions.get((venue, symbol))
            actual = position.quantity if position is not None else Decimal("0")
            differences[f"{venue}:{symbol}"] = actual - expected
        cash_equity_difference = pnl.total_equity - (self.initial_cash + pnl.total_pnl)
        conserved = cash_equity_difference == 0 and all(
            difference == 0 for difference in differences.values()
        )
        return ConservationReport(
            cash_equity_difference=cash_equity_difference,
            asset_quantity_differences=differences,
            duplicate_fill_ids_ignored=self.duplicate_fill_ids_ignored,
            conserved=conserved,
        )

    def asset_balances(self) -> dict[str, Decimal]:
        """Return deterministic ending asset quantities."""

        return {
            f"{venue}:{symbol}": position.quantity
            for (venue, symbol), position in sorted(self._positions.items())
        }

    def currency_balances(self) -> dict[str, Decimal]:
        """Return deterministic ending quote-currency balances."""

        return {self.base_currency: self.cash}
