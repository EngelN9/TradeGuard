"""Replay-level ordering and corporate-action regression tests."""

import pytest
from tests.backtest_factories import crypto_order, plan

from tradeguard.backtest.event_loop import TimelineKind, build_timeline
from tradeguard.data.fixtures import build_fixture


@pytest.mark.replay
def test_timeline_order_is_independent_of_input_record_order() -> None:
    package = build_fixture("normal")
    reversed_package = package.model_copy(update={"records": tuple(reversed(package.records))})

    first, _ = build_timeline(package, plan(crypto_order()))
    second, _ = build_timeline(reversed_package, plan(crypto_order()))

    assert [event.ordering_key for event in first] == [event.ordering_key for event in second]
    same_time = [
        event.kind for event in first if event.event_time_utc == crypto_order().submitted_at_utc
    ]
    assert same_time == [TimelineKind.ORDER, TimelineKind.BAR]


@pytest.mark.replay
def test_stock_split_is_ordered_before_post_split_bar() -> None:
    timeline, ignored = build_timeline(build_fixture("stock_split"), plan())
    kinds = [event.kind for event in timeline]

    assert ignored == 0
    assert kinds == [TimelineKind.BAR, TimelineKind.CORPORATE_ACTION, TimelineKind.BAR]
