"""Unit tests for separate conservative equity and crypto costs."""

from decimal import Decimal

import pytest
from pydantic import ValidationError

from tradeguard.costs.models import CostBreakdown, CryptoCostModel, EquityCostModel
from tradeguard.domain.events import OrderType, Side


@pytest.mark.unit
def test_equity_costs_include_sell_tax_and_market_friction() -> None:
    model = EquityCostModel()
    buy = model.calculate(
        side=Side.BUY,
        order_type=OrderType.MARKET,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )
    sell = model.calculate(
        side=Side.SELL,
        order_type=OrderType.MARKET,
        price=Decimal("100"),
        quantity=Decimal("10"),
    )

    assert buy.commission == Decimal("1")
    assert buy.spread > 0 and buy.slippage > 0 and buy.market_impact > 0
    assert buy.tax == 0
    assert sell.tax == Decimal("3")
    assert sell.total > buy.total


@pytest.mark.unit
def test_crypto_limit_uses_maker_fee_without_market_friction() -> None:
    costs = CryptoCostModel().calculate(
        side=Side.BUY,
        order_type=OrderType.LIMIT,
        price=Decimal("100"),
        quantity=Decimal("1"),
    )

    assert costs.commission == Decimal("0.4")
    assert costs.spread == costs.slippage == costs.market_impact == 0
    assert costs.total == Decimal("0.4")


@pytest.mark.unit
def test_cost_breakdown_rejects_inconsistent_or_float_values() -> None:
    with pytest.raises(ValidationError, match="cost total"):
        CostBreakdown(
            commission=Decimal("1"),
            tax=Decimal("0"),
            spread=Decimal("0"),
            slippage=Decimal("0"),
            market_impact=Decimal("0"),
            total=Decimal("2"),
        )
    with pytest.raises(ValidationError, match="binary floats"):
        EquityCostModel(commission_rate=0.1)
