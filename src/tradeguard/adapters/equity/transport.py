"""Small injectable HTTPS transport with response-size enforcement."""

from __future__ import annotations

import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urlsplit

from tradeguard.adapters.equity.errors import AdapterFailureCode, EquityAdapterError


@dataclass(frozen=True, slots=True)
class HttpRequest:
    method: str
    url: str
    headers: dict[str, str]
    timeout_seconds: float
    max_response_bytes: int


@dataclass(frozen=True, slots=True)
class HttpResponse:
    status_code: int
    headers: dict[str, str]
    body: bytes


class HttpTransport(Protocol):
    def send(self, request: HttpRequest) -> HttpResponse:
        """Send one already-validated HTTPS request."""


class UrllibHttpsTransport:
    """Production transport; host/path policy is rechecked before network I/O."""

    _allowed_host = "api.twelvedata.com"
    _allowed_paths = frozenset({"/time_series"})

    def send(self, request: HttpRequest) -> HttpResponse:
        _validate_request_target(request)
        url_request = urllib.request.Request(  # noqa: S310 - exact HTTPS target validated
            request.url,
            headers=request.headers,
            method=request.method,
        )
        try:
            with urllib.request.urlopen(  # noqa: S310 - exact HTTPS host/path validated above
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
            raise EquityAdapterError(
                AdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE,
                "approved market-data provider is unavailable",
            ) from exc


def _validate_request_target(request: HttpRequest) -> None:
    target = urlsplit(request.url)
    if (
        request.method != "GET"
        or target.scheme != "https"
        or target.hostname != UrllibHttpsTransport._allowed_host
        or target.port not in (None, 443)
        or target.username is not None
        or target.password is not None
        or target.path not in UrllibHttpsTransport._allowed_paths
    ):
        raise EquityAdapterError(
            AdapterFailureCode.FAIL_SCOPE_VIOLATION,
            "request target is outside the approved HTTPS allowlist",
        )
    query_names = {item.partition("=")[0].lower() for item in target.query.split("&") if item}
    if "apikey" in query_names:
        raise EquityAdapterError(
            AdapterFailureCode.FAIL_SCOPE_VIOLATION,
            "credentials are prohibited in request URLs",
        )


def _read_response(
    *,
    status_code: int,
    headers: dict[str, str],
    body_reader: Callable[[int], bytes],
    max_response_bytes: int,
) -> HttpResponse:
    normalized_headers = {key.lower(): value for key, value in headers.items()}
    content_length = normalized_headers.get("content-length")
    if content_length is not None:
        try:
            parsed_length = int(content_length)
            if parsed_length < 0:
                raise ValueError
            if parsed_length > max_response_bytes:
                raise EquityAdapterError(
                    AdapterFailureCode.FAIL_RESPONSE_TOO_LARGE,
                    "provider response exceeds the reviewed size limit",
                )
        except ValueError as exc:
            raise EquityAdapterError(
                AdapterFailureCode.FAIL_SCHEMA_DRIFT,
                "provider returned an invalid content-length header",
            ) from exc
    body = body_reader(max_response_bytes + 1)
    if len(body) > max_response_bytes:
        raise EquityAdapterError(
            AdapterFailureCode.FAIL_RESPONSE_TOO_LARGE,
            "provider response exceeds the reviewed size limit",
        )
    return HttpResponse(status_code=status_code, headers=normalized_headers, body=body)
