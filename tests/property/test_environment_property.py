"""Property tests for the environment allowlist."""

import pytest
from hypothesis import given
from hypothesis import strategies as st

from tradeguard.runtime import RuntimeEnvironment, UnsafeEnvironmentError, load_environment

_ALLOWED = {environment.value for environment in RuntimeEnvironment}


@pytest.mark.property
@given(st.text().filter(lambda value: value.strip().lower() not in _ALLOWED))
def test_every_non_allowlisted_environment_fails_closed(value: str) -> None:
    with pytest.raises(UnsafeEnvironmentError):
        load_environment(value)


@pytest.mark.property
@given(st.sampled_from(sorted(_ALLOWED)))
def test_every_allowlisted_environment_is_stable(value: str) -> None:
    assert load_environment(value).value == value
