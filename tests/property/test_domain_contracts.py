"""Property tests for canonicalization and fail-closed configuration."""

from datetime import datetime
from decimal import Decimal

import pytest
from hypothesis import given
from hypothesis import strategies as st
from pydantic import SecretStr, ValidationError
from tests.factories import event_fields, quote_event, research_effective_config

from tradeguard.config.models import (
    SecretSettings,
    deterministic_config_hash,
    inspect_effective_config,
    make_effective_config,
)
from tradeguard.domain.events import Quote
from tradeguard.domain.serialization import canonical_json, deterministic_checksum
from tradeguard.runtime import RuntimeEnvironment

_ALLOWED_ENVIRONMENTS = {environment.value for environment in RuntimeEnvironment}


@pytest.mark.property
@given(st.dictionaries(st.text(min_size=1), st.integers(), max_size=20))
def test_same_mapping_has_same_canonical_representation(value: dict[str, int]) -> None:
    reversed_items = dict(reversed(list(value.items())))

    assert canonical_json(value) == canonical_json(reversed_items)
    assert deterministic_checksum(value) == deterministic_checksum(reversed_items)


@pytest.mark.property
@given(st.text(alphabet="abcdefghijklmnopqrstuvwxyz", min_size=16, max_size=64))
def test_secret_never_appears_in_inspection(secret_fragment: str) -> None:
    secret = f"tradeguard-secret-{secret_fragment}-sentinel"
    baseline = research_effective_config()
    config = baseline.config.model_copy(
        update={"secrets": SecretSettings(provider_api_key=SecretStr(secret))}
    )
    effective = make_effective_config(config, sources=baseline.sources)

    assert secret not in str(inspect_effective_config(effective))
    assert deterministic_config_hash(config) == effective.config_hash


@pytest.mark.property
@given(st.datetimes(timezones=st.none()))
def test_every_naive_event_datetime_is_rejected(value: datetime) -> None:
    fields = event_fields()
    fields["event_time_utc"] = value

    with pytest.raises(ValidationError, match="timezone-aware"):
        Quote.build(
            **fields,
            bid_price=Decimal("1"),
            ask_price=Decimal("2"),
            bid_quantity=Decimal("1"),
            ask_quantity=Decimal("1"),
        )


@pytest.mark.property
@given(st.text().filter(lambda value: value not in _ALLOWED_ENVIRONMENTS))
def test_every_unallowlisted_configuration_environment_is_rejected(value: str) -> None:
    payload = research_effective_config().config.model_dump(mode="python")
    payload["environment"]["name"] = value  # type: ignore[index]

    with pytest.raises(ValidationError):
        type(research_effective_config().config).model_validate(payload)


@pytest.mark.property
def test_same_event_input_has_same_checksum() -> None:
    assert quote_event().payload_checksum == quote_event().payload_checksum
