"""Property-based cash and asset conservation checks for Prompt 6."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tradeguard.backtest.models import FillLedgerEntry
from tradeguard.costs.models import CostBreakdown
from tradeguard.domain.events import AssetClass, OrderType, Side
from tradeguard.portfolio.ledger import PortfolioLedger


def _zero_costs() -> CostBreakdown:
    return CostBreakdown.build(
        commission=Decimal("0"),
        tax=Decimal("0"),
        spread=Decimal("0"),
        slippage=Decimal("0"),
        market_impact=Decimal("0"),
    )


@pytest.mark.property
@given(
    price=st.integers(min_value=1, max_value=10_000),
    quantity=st.integers(min_value=1, max_value=100),
    mark=st.integers(min_value=1, max_value=10_000),
)
def test_cash_and_asset_conserve_for_any_exact_buy(price: int, quantity: int, mark: int) -> None:
    decimal_price = Decimal(price)
    decimal_quantity = Decimal(quantity)
    initial_cash = decimal_price * decimal_quantity + Decimal("1000")
    ledger = PortfolioLedger(initial_cash=initial_cash, base_currency="USD")
    fill = FillLedgerEntry(
        fill_id="a" * 64,
        order_id="property-buy",
        asset_class=AssetClass.CRYPTO,
        venue="SYNTH-CRYPTO",
        symbol="BTC-USD",
        side=Side.BUY,
        order_type=OrderType.MARKET,
        event_time_utc=datetime(2024, 1, 1, tzinfo=UTC),
        price=decimal_price,
        quantity=decimal_quantity,
        costs=_zero_costs(),
    )

    ledger.apply_fill(fill)
    _, pnl = ledger.mark(
        event_time_utc=datetime(2024, 1, 2, tzinfo=UTC),
        marks={("SYNTH-CRYPTO", "BTC-USD"): Decimal(mark)},
    )

    assert ledger.conservation_report(pnl).conserved is True
    assert pnl.total_equity == initial_cash + pnl.total_pnl
