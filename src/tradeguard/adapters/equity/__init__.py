"""Provider-neutral equity market-data contracts and reviewed implementations."""

from tradeguard.adapters.equity.protocol import (
    EquityAdapterCapabilities,
    EquityDataset,
    EquityMarketDataAdapter,
    HistoricalBarsRequest,
)
from tradeguard.adapters.equity.twelve_data import TwelveDataEquityAdapter

__all__ = [
    "EquityAdapterCapabilities",
    "EquityDataset",
    "EquityMarketDataAdapter",
    "HistoricalBarsRequest",
    "TwelveDataEquityAdapter",
]
