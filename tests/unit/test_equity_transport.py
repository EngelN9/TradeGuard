"""Unit tests for the exact HTTPS target and response-size boundary."""

from __future__ import annotations

import urllib.request
from typing import ClassVar

import pytest

from tradeguard.adapters.equity.errors import AdapterFailureCode, EquityAdapterError
from tradeguard.adapters.equity.transport import (
    HttpRequest,
    UrllibHttpsTransport,
    _read_response,
)


def _request(
    *,
    url: str = "https://api.twelvedata.com/time_series?symbol=AAPL",
    max_response_bytes: int = 16,
) -> HttpRequest:
    return HttpRequest(
        method="GET",
        url=url,
        headers={"Authorization": "apikey fixture-credential"},
        timeout_seconds=1.0,
        max_response_bytes=max_response_bytes,
    )


class StubResponse:
    status = 200
    headers: ClassVar[dict[str, str]] = {"content-length": "2"}

    def __enter__(self) -> StubResponse:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    @staticmethod
    def read(_: int) -> bytes:
        return b"{}"


@pytest.mark.unit
def test_transport_allows_only_the_exact_https_target(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(urllib.request, "urlopen", lambda *_, **__: StubResponse())
    response = UrllibHttpsTransport().send(_request())

    assert response.status_code == 200
    assert response.body == b"{}"

    for url in (
        "http://api.twelvedata.com/time_series",
        "https://evil.example/time_series",
        "https://api.twelvedata.com/dividends",
        "https://api.twelvedata.com/time_series?apikey=secret",
    ):
        with pytest.raises(EquityAdapterError) as error:
            UrllibHttpsTransport().send(_request(url=url))
        assert error.value.code is AdapterFailureCode.FAIL_SCOPE_VIOLATION


@pytest.mark.unit
def test_transport_maps_network_failure_to_provider_unavailable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail(*_: object, **__: object) -> StubResponse:
        raise TimeoutError

    monkeypatch.setattr(urllib.request, "urlopen", fail)
    with pytest.raises(EquityAdapterError) as error:
        UrllibHttpsTransport().send(_request())

    assert error.value.code is AdapterFailureCode.BLOCKED_PROVIDER_UNAVAILABLE
    assert "fixture-credential" not in str(error.value)


@pytest.mark.unit
def test_response_size_and_content_length_fail_closed() -> None:
    with pytest.raises(EquityAdapterError) as length_error:
        _read_response(
            status_code=200,
            headers={"content-length": "17"},
            body_reader=lambda _: b"",
            max_response_bytes=16,
        )
    assert length_error.value.code is AdapterFailureCode.FAIL_RESPONSE_TOO_LARGE

    with pytest.raises(EquityAdapterError) as body_error:
        _read_response(
            status_code=200,
            headers={},
            body_reader=lambda _: b"x" * 17,
            max_response_bytes=16,
        )
    assert body_error.value.code is AdapterFailureCode.FAIL_RESPONSE_TOO_LARGE

    for content_length in ("invalid", "-1"):
        with pytest.raises(EquityAdapterError) as header_error:
            _read_response(
                status_code=200,
                headers={"content-length": content_length},
                body_reader=lambda _: b"",
                max_response_bytes=16,
            )
        assert header_error.value.code is AdapterFailureCode.FAIL_SCHEMA_DRIFT
