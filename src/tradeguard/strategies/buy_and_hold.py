"""Frozen BTC-USD synthetic buy-and-hold baseline."""

from __future__ import annotations

from uuid import UUID, uuid5

from tradeguard.domain.events import (
    AssetClass,
    OrderType,
    Side,
    Signal,
    TargetPosition,
    TradeProposal,
)
from tradeguard.domain.serialization import deterministic_checksum
from tradeguard.strategies.models import (
    R4_DATASET_ID,
    R4_DATASET_VERSION,
    R4_FIXTURE_SHA256,
    R4_MANIFEST_CHECKSUM,
    R4_STRATEGY_ID,
    R4_SYMBOL,
    R4_VENUE,
    BuyAndHoldParameters,
    StrategyBar,
    StrategyContext,
    StrategyMarket,
    StrategyOutput,
    StrategySpecification,
)

STRATEGY_ID = R4_STRATEGY_ID
STRATEGY_VERSION = "1.0.0"
EXPECTED_DATASET_ID = R4_DATASET_ID
EXPECTED_DATASET_VERSION = R4_DATASET_VERSION
EXPECTED_MANIFEST_CHECKSUM = R4_MANIFEST_CHECKSUM
EXPECTED_FIXTURE_SHA256 = R4_FIXTURE_SHA256
EXPECTED_VENUE = R4_VENUE
EXPECTED_SYMBOL = R4_SYMBOL
REQUIRED_DATA = (
    "asset_class",
    "venue",
    "symbol",
    "event_time_utc",
    "sequence_number",
    "close_price",
)
STRATEGY_UUID_NAMESPACE = UUID("85250338-2176-4f41-a655-a24917728dd2")


def buy_and_hold_specification() -> StrategySpecification:
    """Return the frozen R4 strategy specification."""

    return StrategySpecification(
        strategy_id=STRATEGY_ID,
        strategy_version=STRATEGY_VERSION,
        supported_asset_classes=(AssetClass.CRYPTO,),
        supported_markets=(
            StrategyMarket(
                asset_class=AssetClass.CRYPTO,
                venue=EXPECTED_VENUE,
                symbol=EXPECTED_SYMBOL,
                dataset_id=EXPECTED_DATASET_ID,
                dataset_version=EXPECTED_DATASET_VERSION,
                manifest_checksum=EXPECTED_MANIFEST_CHECKSUM,
            ),
        ),
        required_data=REQUIRED_DATA,
        parameter_schema=BuyAndHoldParameters.model_json_schema(),
        warmup_bars=1,
        allowed_outputs=("Signal", "TargetPosition", "TradeProposal"),
        assumptions=(
            "The research account starts with no BTC position.",
            "One completed synthetic bar is sufficient to submit one fixed-quantity proposal.",
            "The position remains open through the end of the synthetic fixture.",
        ),
        unsupported_markets=(
            "Every asset, venue, symbol, and dataset except synthetic BTC-USD on SYNTH-CRYPTO.",
        ),
        known_limitations=(
            "No benchmark, validation, optimization, risk approval, liquidation, "
            "or performance claim.",
        ),
        failure_modes=(
            "Reject unknown, changed, stale, quarantined, or undeclared market data.",
            "Reject any output outside Signal, TargetPosition, and TradeProposal.",
        ),
    )


class BuyAndHoldBtcUsd:
    """Emit one fixed buy proposal after the first completed declared bar."""

    def __init__(self, parameters: BuyAndHoldParameters) -> None:
        self._parameters = parameters
        self._context: StrategyContext | None = None
        self._emitted = False

    @property
    def specification(self) -> StrategySpecification:
        return buy_and_hold_specification()

    def initialize(self, context: StrategyContext) -> None:
        if self._context is not None:
            raise RuntimeError("strategy instance cannot be initialized twice")
        self._context = context

    def on_event(self, event: StrategyBar) -> tuple[StrategyOutput, ...]:
        if self._context is None:
            raise RuntimeError("strategy must be initialized before receiving events")
        if self._emitted:
            return ()
        if (event.asset_class, event.venue, event.symbol) != (
            self._context.asset_class,
            self._context.venue,
            self._context.symbol,
        ):
            raise ValueError("strategy event market differs from initialized context")

        identity = deterministic_checksum(
            {
                "run_id": self._context.run_id,
                "strategy_version_hash": self._context.strategy_version_hash,
                "event": event,
            }
        )
        signal_id = uuid5(STRATEGY_UUID_NAMESPACE, f"{identity}:signal")
        target_id = uuid5(STRATEGY_UUID_NAMESPACE, f"{identity}:target")
        proposal_id = uuid5(STRATEGY_UUID_NAMESPACE, f"{identity}:proposal")
        base_event = {
            "source": STRATEGY_ID,
            "asset_class": event.asset_class,
            "venue": event.venue,
            "symbol": event.symbol,
            "event_time_utc": event.event_time_utc,
            "ingest_time_utc": event.event_time_utc,
            "correlation_id": self._context.correlation_id,
            "run_id": self._context.run_id,
        }
        signal = Signal.build(
            **base_event,
            event_id=signal_id,
            sequence_number=event.sequence_number * 10 + 1,
            signal_name="buy-and-hold-entry",
            direction=1,
            strength=1,
        )
        target = TargetPosition.build(
            **base_event,
            event_id=target_id,
            causation_id=signal.event_id,
            sequence_number=event.sequence_number * 10 + 2,
            target_quantity=self._parameters.quantity,
            rationale="Frozen synthetic buy-and-hold target; no risk approval implied.",
        )
        proposal = TradeProposal.build(
            **base_event,
            event_id=proposal_id,
            causation_id=target.event_id,
            sequence_number=event.sequence_number * 10 + 3,
            side=Side.BUY,
            order_type=OrderType.MARKET,
            quantity=self._parameters.quantity,
        )
        self._emitted = True
        return signal, target, proposal

    def finalize(self) -> tuple[StrategyOutput, ...]:
        if self._context is None:
            raise RuntimeError("strategy must be initialized before finalization")
        return ()
