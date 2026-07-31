"""Deterministic reviewed equity-session registry.

Unknown dates are never inferred to be open. A release candidate must extend and
review this registry for its connected observation window before it can PASS.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import UTC, date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

from tradeguard.data.models import MarketSession, SessionStatus


class MarketCalendarUnavailableError(ValueError):
    """Raised when a session date is absent from the reviewed registry."""


class ReviewedCalendarDocument(BaseModel):
    """Versioned, human-reviewable connected-session registry document."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    schema_version: Literal["1.0.0"] = "1.0.0"
    review_status: Literal["BLOCKED_PENDING_SESSION_REVIEW", "APPROVED"]
    reviewed_by: str | None = None
    reviewed_at: date | None = None
    sessions: tuple[MarketSession, ...] = ()

    def to_registry(self) -> DeterministicMicCalendarRegistry:
        if self.review_status != "APPROVED" or not self.sessions:
            raise MarketCalendarUnavailableError(
                "BLOCKED_MARKET_CALENDAR: connected session registry is not approved"
            )
        return DeterministicMicCalendarRegistry(self.sessions)


class DeterministicMicCalendarRegistry:
    """Exact MIC/date lookup with no weekday or holiday inference."""

    def __init__(self, sessions: Iterable[MarketSession] = ()) -> None:
        indexed: dict[tuple[str, date], MarketSession] = {}
        for session in sessions:
            key = (session.venue, _session_date(session))
            if key in indexed:
                raise ValueError("duplicate reviewed market session")
            indexed[key] = session
        self._sessions = indexed

    def require_session(self, mic: str, session_date: date) -> MarketSession:
        """Return one exact reviewed session or fail closed."""

        try:
            return self._sessions[(mic, session_date)]
        except KeyError as exc:
            raise MarketCalendarUnavailableError(
                f"BLOCKED_MARKET_CALENDAR: no reviewed {mic} session for {session_date.isoformat()}"
            ) from exc

    def sessions_between(
        self,
        mic: str,
        start_date: date,
        end_date: date,
    ) -> tuple[MarketSession, ...]:
        """Return registered sessions in a closed date interval."""

        if end_date < start_date:
            raise ValueError("end_date must not precede start_date")
        return tuple(
            session
            for (venue, session_date), session in sorted(self._sessions.items())
            if venue == mic and start_date <= session_date <= end_date
        )


def fixture_calendar_registry() -> DeterministicMicCalendarRegistry:
    """Return the reviewed synthetic-contract window for both accepted AAPL MICs."""

    dates = (
        date(2024, 1, 2),
        date(2024, 1, 3),
        date(2024, 1, 4),
        date(2024, 1, 5),
        date(2024, 1, 8),
        date(2024, 1, 9),
        date(2024, 1, 10),
    )
    known_at = datetime(2023, 12, 1, tzinfo=UTC)
    sessions = [
        MarketSession(
            source="tradeguard-reviewed-session-registry",
            venue=mic,
            session_calendar=mic,
            session_open_utc=datetime(
                session_date.year,
                session_date.month,
                session_date.day,
                14,
                30,
                tzinfo=UTC,
            ),
            session_close_utc=datetime(
                session_date.year,
                session_date.month,
                session_date.day,
                21,
                0,
                tzinfo=UTC,
            ),
            known_at=known_at,
            status=SessionStatus.OPEN,
        )
        for mic in ("XNAS", "XNGS")
        for session_date in dates
    ]
    return DeterministicMicCalendarRegistry(sessions)


def _session_date(session: MarketSession) -> date:
    """Map the reviewed US-equity UTC close to its exchange-local session date."""

    return session.session_open_utc.date()
