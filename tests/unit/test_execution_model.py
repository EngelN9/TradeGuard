"""Direct tests for every conservative execution gate."""

from datetime import UTC, datetime
from decimal import Decimal

import pytest
from tests.backtest_factories import crypto_order, equity_order

from tradeguard.costs.models import CryptoCostModel, EquityCostModel
from tradeguard.data.fixtures import build_fixture
from tradeguard.data.models import MARKET_RECORD_ADAPTER, OHLCVBar
from tradeguard.domain.events import OrderType, Side
from tradeguard.execution_models.conservative import (
    ConservativeBarExecutionModel,
    ExecutionDecision,
    ExecutionDisposition,
)


def _bar(scenario: str, index: int = -1) -> OHLCVBar:
    record = MARKET_RECORD_ADAPTER.validate_python(build_fixture(scenario).records[index])
    assert isinstance(record, OHLCVBar)
    return record


def _evaluate(
    *,
    order=None,
    bar=None,
    package=None,
    latency_seconds: int = 1,
    remaining: str = "0.1000",
) -> ExecutionDecision:
    selected_package = package or build_fixture("normal")
    selected_bar = bar or _bar("normal")
    return ConservativeBarExecutionModel().evaluate(
        order=order or crypto_order(),
        remaining_quantity=Decimal(remaining),
        bar=selected_bar,
        metadata=selected_package.instrument_metadata[0],
        knowledge_time_utc=selected_package.policy.knowledge_time_utc,
        latency_seconds=latency_seconds,
        max_participation_rate=Decimal("0.25"),
        equity_costs=EquityCostModel(),
        crypto_costs=CryptoCostModel(),
        market_sessions=selected_package.market_sessions,
        maintenance_intervals=selected_package.maintenance_intervals,
    )


@pytest.mark.unit
def test_identity_metadata_and_latency_gates() -> None:
    different = crypto_order().model_copy(update={"symbol": "ETH-USD"})
    inactive_package = build_fixture("normal")
    inactive_metadata = inactive_package.instrument_metadata[0].model_copy(
        update={"active_to": datetime(2023, 1, 1, tzinfo=UTC)}
    )
    inactive_package = inactive_package.model_copy(
        update={"instrument_metadata": (inactive_metadata,)}
    )

    assert _evaluate(order=different).reason == "different_instrument"
    assert _evaluate(package=inactive_package).reason == "metadata_unknown_or_inactive"
    assert _evaluate(latency_seconds=60).reason == "latency_not_elapsed"


@pytest.mark.unit
def test_session_maintenance_and_liquidity_block() -> None:
    equity_package = build_fixture("stock_split").model_copy(update={"market_sessions": ()})
    equity_bar = _bar("stock_split", 0)
    maintenance_package = build_fixture("crypto_maintenance")
    maintenance_bar = _bar("crypto_maintenance")
    before_maintenance = crypto_order(submitted_at=datetime(2024, 1, 2, 0, 2, tzinfo=UTC))
    zero_volume = _bar("normal").model_copy(update={"volume": Decimal("0")})

    assert (
        _evaluate(
            order=equity_order(),
            bar=equity_bar,
            package=equity_package,
            remaining="10",
        ).reason
        == "equity_session_closed_or_unknown"
    )
    assert (
        _evaluate(
            order=before_maintenance,
            bar=maintenance_bar,
            package=maintenance_package,
        ).reason
        == "venue_maintenance"
    )
    assert _evaluate(bar=zero_volume).reason == "insufficient_bar_liquidity"


@pytest.mark.unit
def test_precision_minimum_limit_and_sell_prices_are_conservative() -> None:
    precision = crypto_order(quantity="0.10005")
    minimum = crypto_order(quantity="0.0500")
    below_quantity = crypto_order(quantity="0.00001")
    missed = crypto_order(
        quantity="0.2000",
        order_type=OrderType.LIMIT,
        limit_price="98.00",
    )
    sell = crypto_order(side=Side.SELL, quantity="0.2000")
    limit_sell = crypto_order(
        side=Side.SELL,
        quantity="0.2000",
        order_type=OrderType.LIMIT,
        limit_price="101.50",
    )

    assert _evaluate(order=precision).reason == "order_precision_rejected"
    assert _evaluate(order=minimum).reason == "minimum_notional_rejected"
    assert _evaluate(order=below_quantity).reason == "minimum_quantity_rejected"
    assert _evaluate(order=missed).reason == "limit_not_crossed"
    assert _evaluate(order=sell, remaining="0.2000").price == Decimal("99.00")
    decision = _evaluate(order=limit_sell, remaining="0.2000")
    assert decision.disposition is ExecutionDisposition.FILL
    assert decision.price == Decimal("101.50")
