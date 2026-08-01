"""Negative tests for the exact Coinbase public REST transport boundary."""

import pytest

from tradeguard.adapters.crypto.errors import CryptoAdapterError, CryptoAdapterFailureCode
from tradeguard.adapters.crypto.transport import (
    RestRequest,
    _read_response,
    validate_public_request,
)


def _request(url: str, *, method: str = "GET", headers: dict[str, str] | None = None):
    return RestRequest(
        method=method,
        url=url,
        headers=headers or {"Accept": "application/json"},
        timeout_seconds=1,
        max_response_bytes=100,
    )


@pytest.mark.unit
@pytest.mark.parametrize(
    "target_request",
    [
        _request("http://api.coinbase.com/api/v3/brokerage/time"),
        _request("https://evil.example/api/v3/brokerage/time"),
        _request("https://api.coinbase.com/api/v3/brokerage/orders"),
        _request("https://api.coinbase.com/api/v3/brokerage/time", method="POST"),
        _request(
            "https://api.coinbase.com/api/v3/brokerage/time",
            headers={"Authorization": "Bearer prohibited"},
        ),
        _request("https://api.coinbase.com/api/v3/brokerage/time?unexpected=true"),
        _request(
            "https://api.coinbase.com/api/v3/brokerage/market/products/BTC-USD/ticker"
            "?limit=1&limit=2"
        ),
    ],
)
def test_unapproved_rest_surface_is_rejected(target_request: RestRequest) -> None:
    with pytest.raises(CryptoAdapterError) as error:
        validate_public_request(target_request)
    assert error.value.code is CryptoAdapterFailureCode.FAIL_SCOPE_VIOLATION


@pytest.mark.unit
def test_bounded_response_reader_accepts_small_body_and_normalizes_headers() -> None:
    response = _read_response(
        status_code=200,
        headers={"Content-Length": "2", "X-Test": "yes"},
        body_reader=lambda limit: b"{}",
        max_response_bytes=2,
    )
    assert response.body == b"{}"
    assert response.headers == {"content-length": "2", "x-test": "yes"}


@pytest.mark.unit
@pytest.mark.parametrize(
    ("headers", "body", "expected_code"),
    [
        ({"content-length": "invalid"}, b"{}", CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT),
        ({"content-length": "-1"}, b"{}", CryptoAdapterFailureCode.FAIL_SCHEMA_DRIFT),
        ({"content-length": "3"}, b"{}", CryptoAdapterFailureCode.FAIL_RESPONSE_TOO_LARGE),
        ({}, b"123", CryptoAdapterFailureCode.FAIL_RESPONSE_TOO_LARGE),
    ],
)
def test_bounded_response_reader_rejects_invalid_or_oversized_body(
    headers: dict[str, str],
    body: bytes,
    expected_code: CryptoAdapterFailureCode,
) -> None:
    with pytest.raises(CryptoAdapterError) as error:
        _read_response(
            status_code=200,
            headers=headers,
            body_reader=lambda limit: body,
            max_response_bytes=2,
        )
    assert error.value.code is expected_code
