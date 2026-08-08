"""Unit tests for Decimal cash, asset, PnL, and action accounting."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from tradeguard.backtest.models import FillLedgerEntry
from tradeguard.costs.models import CostBreakdown
from tradeguard.data.fixtures import build_fixture
from tradeguard.data.models import CorporateAction, CorporateActionType
from tradeguard.domain.events import AssetClass, OrderType, Side
from tradeguard.portfolio.ledger import (
    InsufficientCashError,
    InsufficientPositionError,
    PortfolioLedger,
)

NOW = datetime(2024, 1, 2, tzinfo=UTC)


def _fill(
    *,
    fill_id: str,
    side: Side,
    quantity: str,
    price: str,
    total_cost: str = "0",
) -> FillLedgerEntry:
    total = Decimal(total_cost)
    return FillLedgerEntry(
        fill_id=fill_id * 64,
        order_id=f"order-{fill_id}",
        asset_class=AssetClass.EQUITY,
        venue="SYNTH-XNYS",
        symbol="ACME",
        side=side,
        order_type=OrderType.MARKET,
        event_time_utc=NOW,
        price=Decimal(price),
        quantity=Decimal(quantity),
        costs=CostBreakdown.build(
            commission=total,
            tax=Decimal("0"),
            spread=Decimal("0"),
            slippage=Decimal("0"),
            market_impact=Decimal("0"),
        ),
    )


@pytest.mark.unit
def test_fill_is_idempotent_and_cash_asset_conserve() -> None:
    ledger = PortfolioLedger(initial_cash=Decimal("1000"), base_currency="USD")
    fill = _fill(fill_id="a", side=Side.BUY, quantity="2", price="100", total_cost="1")

    assert ledger.apply_fill(fill) is True
    assert ledger.apply_fill(fill) is False
    positions, pnl = ledger.mark(event_time_utc=NOW, marks={("SYNTH-XNYS", "ACME"): Decimal("110")})
    report = ledger.conservation_report(pnl)

    assert ledger.cash == Decimal("799")
    assert positions[0].quantity == Decimal("2")
    assert pnl.total_equity == Decimal("1019")
    assert report.conserved is True
    assert report.duplicate_fill_ids_ignored == 1


@pytest.mark.unit
def test_sell_realizes_pnl_and_prevents_short_or_negative_cash() -> None:
    ledger = PortfolioLedger(initial_cash=Decimal("1000"), base_currency="USD")
    ledger.apply_fill(_fill(fill_id="a", side=Side.BUY, quantity="2", price="100"))
    ledger.apply_fill(_fill(fill_id="b", side=Side.SELL, quantity="1", price="120", total_cost="1"))
    _, pnl = ledger.mark(event_time_utc=NOW, marks={("SYNTH-XNYS", "ACME"): Decimal("120")})

    assert ledger.realized_pnl == Decimal("19")
    assert pnl.total_pnl == Decimal("39")
    with pytest.raises(InsufficientPositionError):
        ledger.apply_fill(_fill(fill_id="c", side=Side.SELL, quantity="2", price="120"))
    poor = PortfolioLedger(initial_cash=Decimal("10"), base_currency="USD")
    with pytest.raises(InsufficientCashError):
        poor.apply_fill(_fill(fill_id="d", side=Side.BUY, quantity="1", price="100"))


@pytest.mark.unit
def test_stock_split_preserves_cost_basis_and_is_idempotent() -> None:
    ledger = PortfolioLedger(initial_cash=Decimal("10000"), base_currency="USD")
    ledger.apply_fill(_fill(fill_id="a", side=Side.BUY, quantity="10", price="100"))
    action = build_fixture("stock_split").corporate_actions[0]

    record = ledger.apply_corporate_action(action)
    duplicate = ledger.apply_corporate_action(action)
    positions, pnl = ledger.mark(
        event_time_utc=action.effective_at,
        marks={("SYNTH-XNYS", "ACME"): Decimal("50")},
    )

    assert record is not None and record.quantity_after == Decimal("20")
    assert duplicate is None
    assert positions[0].average_cost == Decimal("50")
    assert pnl.total_pnl == 0
    assert ledger.conservation_report(pnl).conserved is True


@pytest.mark.unit
def test_dividend_symbol_change_and_delisting_are_auditable() -> None:
    ledger = PortfolioLedger(initial_cash=Decimal("10000"), base_currency="USD")
    ledger.apply_fill(_fill(fill_id="a", side=Side.BUY, quantity="10", price="100"))
    base = {
        "source": "synthetic",
        "venue": "SYNTH-XNYS",
        "symbol": "ACME",
        "effective_at": NOW,
        "known_at": NOW,
        "action_version": "test-v1",
    }
    dividend = CorporateAction(
        **base,
        action_type=CorporateActionType.CASH_DIVIDEND,
        cash_amount=Decimal("1"),
        currency="USD",
    )
    symbol_change = CorporateAction(
        **base,
        action_type=CorporateActionType.SYMBOL_CHANGE,
        new_symbol="ACM2",
    )
    delisting = CorporateAction(
        **(base | {"symbol": "ACM2"}),
        action_type=CorporateActionType.DELISTING,
    )

    assert ledger.apply_corporate_action(dividend).cash_delta == Decimal("10")  # type: ignore[union-attr]
    assert ledger.apply_corporate_action(symbol_change).symbol_after == "ACM2"  # type: ignore[union-attr]
    assert ledger.apply_corporate_action(delisting) is not None
    assert ledger.asset_balances() == {"SYNTH-XNYS:ACM2": Decimal("10")}
    assert ledger.currency_balances() == {"USD": Decimal("9010")}


@pytest.mark.unit
def test_invalid_ledger_and_corporate_action_inputs_fail_closed() -> None:
    with pytest.raises(ValueError, match="positive"):
        PortfolioLedger(initial_cash=Decimal("0"), base_currency="USD")
    with pytest.raises(ValueError, match="empty"):
        PortfolioLedger(initial_cash=Decimal("1"), base_currency="")
    ledger = PortfolioLedger(initial_cash=Decimal("100"), base_currency="USD")
    base = {
        "source": "synthetic",
        "venue": "SYNTH-XNYS",
        "symbol": "ACME",
        "effective_at": NOW,
        "known_at": NOW,
        "action_version": "test-v1",
    }
    with pytest.raises(ValueError, match="positive ratio"):
        ledger.apply_corporate_action(
            CorporateAction(**base, action_type=CorporateActionType.SPLIT)
        )
    with pytest.raises(ValueError, match="currency"):
        ledger.apply_corporate_action(
            CorporateAction(
                **base,
                action_type=CorporateActionType.CASH_DIVIDEND,
                cash_amount=Decimal("1"),
                currency="EUR",
            )
        )
    with pytest.raises(ValueError, match="new_symbol"):
        ledger.apply_corporate_action(
            CorporateAction(**base, action_type=CorporateActionType.SYMBOL_CHANGE)
        )
