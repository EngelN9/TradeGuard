"""Injectable Coinbase HTTPS transport with an exact public-only allowlist."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import parse_qs, urlsplit

from tradeguard.adapters.crypto.errors import (
    CryptoAdapterError,
    CryptoAdapterFailureCode,
    CryptoScopeViolationError,
)

_ALLOWED_HOST = "api.coinbase.com"
_ALLOWED_PATHS = frozenset(
    {
        "/api/v3/brokerage/time",
        "/api/v3/brokerage/market/products/BTC-USD",
        "/api/v3/brokerage/market/products/BTC-USD/candles",
        "/api/v3/brokerage/market/products/BTC-USD/ticker",
    }
)
_ALLOWED_QUERY_NAMES = {
    "/api/v3/brokerage/time": frozenset(),
    "/api/v3/brokerage/market/products/BTC-USD": frozenset(),
    "/api/v3/brokerage/market/products/BTC-USD/candles": frozenset(
        {"start", "end", "granularity", "limit"}
    ),
    "/api/v3/brokerage/market/products/BTC-USD/ticker": frozenset({"limit"}),
}
_PROHIBITED_HEADERS = frozenset({"authorization", "cookie", "proxy-authorization"})


@dataclass(frozen=True, slots=True)
class RestRequest:
    method: str
    url: str
    headers: dict[str, str]
    timeout_seconds: float
    max_response_bytes: int


@dataclass(frozen=True, slots=True)
class RestResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes


class RestTransport(Protocol):
    def send(self, request: RestRequest) -> RestResponse:
        """Send one already-scoped public HTTPS request."""


class CoinbasePublicHttpsTransport:
    """Production REST transport; policy is checked again immediately before I/O."""

    def send(self, request: RestRequest) -> RestResponse:
        validate_public_request(request)
        url_request = urllib.request.Request(  # noqa: S310 - exact HTTPS target validated
            request.url,
            headers=request.headers,
            method=request.method,
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - exact HTTPS target validated
                url_request,
                timeout=request.timeout_seconds,
            ) as response:
                return _read_response(
                    status_code=response.status,
                    headers=dict(response.headers.items()),
                    body_reader=response.read,
                    max_response_bytes=request.max_response_bytes,
                )
        except urllib.error.HTTPError as exc:
            return _read_response(
                status_code=exc.code,
                headers=dict(exc.headers.items()),
                body_reader=exc.read,
                max_response_bytes=request.max_response_bytes,
            )
        except (TimeoutError, urllib.error.URLError, OSError) as exc:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE,
                "approved public market-data provider is unavailable",
            ) from exc


def validate_public_request(request: RestRequest) -> None:
    """Reject anything outside the exact unauthenticated public GET surface."""

    target = urlsplit(request.url)
    if (
        request.method != "GET"
        or target.scheme != "https"
        or target.hostname != _ALLOWED_HOST
        or target.port not in (None, 443)
        or target.username is not None
        or target.password is not None
        or target.fragment
        or target.path not in _ALLOWED_PATHS
    ):
        raise CryptoScopeViolationError("request target is outside the public REST allowlist")
    header_names = {name.strip().lower() for name in request.headers}
    if header_names & _PROHIBITED_HEADERS:
        raise CryptoScopeViolationError("authentication and session headers are prohibited")
    query = parse_qs(target.query, keep_blank_values=True)
    if set(query) - _ALLOWED_QUERY_NAMES[target.path]:
        raise CryptoScopeViolationError("request contains an unreviewed query parameter")
    if any(len(values) != 1 for values in query.values()):
        raise CryptoScopeViolationError("duplicate public query parameters are prohibited")


def _read_response(
    *,
    status_code: int,
    headers: dict[str, str],
    body_reader: Callable[[int], bytes],
    max_response_bytes: int,
) -> RestResponse:
    normalized_headers = {key.lower(): value for key, value in headers.items()}
    content_length = normalized_headers.get("content-length")
    if content_length is not None:
        try:
            parsed_length = int(content_length)
            if parsed_length < 0:
                raise ValueError
        except ValueError as exc:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider returned an invalid content-length header",
            ) from exc
        if parsed_length > max_response_bytes:
            raise CryptoAdapterError(
                CryptoAdapterFailureCode.FAIL_RESPONSE_TOO_LARGE,
                "provider response exceeds the reviewed size limit",
            )
    body = body_reader(max_response_bytes + 1)
    if len(body) > max_response_bytes:
        raise CryptoAdapterError(
            CryptoAdapterFailureCode.FAIL_RESPONSE_TOO_LARGE,
            "provider response exceeds the reviewed size limit",
        )
    return RestResponse(status_code=status_code, headers=normalized_headers, body=body)
