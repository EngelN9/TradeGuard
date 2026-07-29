"""Run the deterministic mock market-data service."""

from __future__ import annotations

import uvicorn


def main() -> None:
    """Start the mock market-data server."""

    uvicorn.run("tradeguard.mock_market_data.app:app", host="0.0.0.0", port=8001)


if __name__ == "__main__":
    main()
