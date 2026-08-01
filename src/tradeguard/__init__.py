"""TradeGuard safety-first research platform."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("tradeguard") or "0.1.0.dev0"
except PackageNotFoundError:
    __version__ = "0.1.0.dev0"

__all__ = ["__version__"]
