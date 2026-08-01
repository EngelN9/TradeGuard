"""Run the deterministic paper-broker skeleton."""

from __future__ import annotations

import uvicorn


def main() -> None:
    """Start the paper-broker service."""

    uvicorn.run("tradeguard.paper_broker.app:app", host="0.0.0.0", port=8002)


if __name__ == "__main__":
    main()
