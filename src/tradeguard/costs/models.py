"""Decimal-only equity and crypto cost models for deterministic research."""

from __future__ import annotations

from decimal import Decimal
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator

from tradeguard.domain.events import OrderType, Side
from tradeguard.domain.serialization import AuthorityDecimal

NonNegativeDecimal = Annotated[AuthorityDecimal, Field(ge=0)]
_BASIS_POINTS = 10_000


class CostModel(BaseModel):
    """Strict immutable base for authoritative cost assumptions."""

    model_config = ConfigDict(frozen=True, extra="forbid", validate_default=True)


class CostBreakdown(CostModel):
    """Explicit costs charged in the account's quote currency."""

    commission: NonNegativeDecimal
    tax: NonNegativeDecimal
    spread: NonNegativeDecimal
    slippage: NonNegativeDecimal
    market_impact: NonNegativeDecimal
    total: NonNegativeDecimal

    @model_validator(mode="after")
    def validate_total(self) -> Self:
        expected = self.commission + self.tax + self.spread + self.slippage + self.market_impact
        if self.total != expected:
            raise ValueError("cost total must equal the explicit cost components")
        return self

    @classmethod
    def build(
        cls,
        *,
        commission: AuthorityDecimal,
        tax: AuthorityDecimal,
        spread: AuthorityDecimal,
        slippage: AuthorityDecimal,
        market_impact: AuthorityDecimal,
    ) -> CostBreakdown:
        values = (commission, tax, spread, slippage, market_impact)
        return cls(
            commission=commission,
            tax=tax,
            spread=spread,
            slippage=slippage,
            market_impact=market_impact,
            total=sum(values, start=Decimal("0")),
        )


class EquityCostModel(CostModel):
    """Conservative cash-equity commission, tax, and execution assumptions."""

    version: Literal["equity-conservative-v1"] = "equity-conservative-v1"
    commission_rate: NonNegativeDecimal = Decimal("0.001")
    minimum_commission: NonNegativeDecimal = Decimal("1")
    sell_tax_rate: NonNegativeDecimal = Decimal("0.003")
    spread_bps: NonNegativeDecimal = Decimal("5")
    slippage_bps: NonNegativeDecimal = Decimal("5")
    market_impact_bps: NonNegativeDecimal = Decimal("5")

    def calculate(
        self,
        *,
        side: Side,
        order_type: OrderType,
        price: AuthorityDecimal,
        quantity: AuthorityDecimal,
    ) -> CostBreakdown:
        notional = price * quantity
        commission = max(notional * self.commission_rate, self.minimum_commission)
        tax = notional * self.sell_tax_rate if side is Side.SELL else Decimal("0")
        return _execution_costs(
            commission=commission,
            tax=tax,
            notional=notional,
            order_type=order_type,
            spread_bps=self.spread_bps,
            slippage_bps=self.slippage_bps,
            market_impact_bps=self.market_impact_bps,
        )


class CryptoCostModel(CostModel):
    """Conservative spot-only maker/taker and execution assumptions."""

    version: Literal["crypto-spot-conservative-v1"] = "crypto-spot-conservative-v1"
    maker_fee_rate: NonNegativeDecimal = Decimal("0.004")
    taker_fee_rate: NonNegativeDecimal = Decimal("0.006")
    spread_bps: NonNegativeDecimal = Decimal("8")
    slippage_bps: NonNegativeDecimal = Decimal("8")
    market_impact_bps: NonNegativeDecimal = Decimal("8")

    def calculate(
        self,
        *,
        side: Side,
        order_type: OrderType,
        price: AuthorityDecimal,
        quantity: AuthorityDecimal,
    ) -> CostBreakdown:
        del side  # Spot fees are symmetric in this v1 research model.
        notional = price * quantity
        fee_rate = self.maker_fee_rate if order_type is OrderType.LIMIT else self.taker_fee_rate
        return _execution_costs(
            commission=notional * fee_rate,
            tax=Decimal("0"),
            notional=notional,
            order_type=order_type,
            spread_bps=self.spread_bps,
            slippage_bps=self.slippage_bps,
            market_impact_bps=self.market_impact_bps,
        )


def _execution_costs(  # noqa: PLR0913 - cost components remain explicit and auditable
    *,
    commission: AuthorityDecimal,
    tax: AuthorityDecimal,
    notional: AuthorityDecimal,
    order_type: OrderType,
    spread_bps: AuthorityDecimal,
    slippage_bps: AuthorityDecimal,
    market_impact_bps: AuthorityDecimal,
) -> CostBreakdown:
    market_multiplier = Decimal("1") if order_type is OrderType.MARKET else Decimal("0")
    denominator = Decimal(_BASIS_POINTS)
    return CostBreakdown.build(
        commission=commission,
        tax=tax,
        spread=notional * spread_bps / denominator * market_multiplier,
        slippage=notional * slippage_bps / denominator * market_multiplier,
        market_impact=notional * market_impact_bps / denominator * market_multiplier,
    )
