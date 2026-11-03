"""The failed-login throttle, with a clock the tests move by hand."""

from app.services.login_throttle import LoginThrottle


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def throttle_with_clock() -> tuple[LoginThrottle, FakeClock]:
    clock = FakeClock()
    return LoginThrottle(max_failures=3, window_seconds=60, clock=clock), clock


def test_an_address_is_refused_at_the_limit() -> None:
    throttle, _ = throttle_with_clock()
    for _ in range(2):
        throttle.record_failure("1.2.3.4")
    assert not throttle.is_refused("1.2.3.4")

    throttle.record_failure("1.2.3.4")

    assert throttle.is_refused("1.2.3.4")


def test_other_addresses_are_unaffected() -> None:
    throttle, _ = throttle_with_clock()
    for _ in range(3):
        throttle.record_failure("1.2.3.4")

    assert not throttle.is_refused("5.6.7.8")


def test_failures_expire_one_by_one() -> None:
    """A sliding window: each failure ages out on its own schedule."""
    throttle, clock = throttle_with_clock()
    throttle.record_failure("1.2.3.4")
    clock.now += 30
    throttle.record_failure("1.2.3.4")
    throttle.record_failure("1.2.3.4")
    assert throttle.retry_after("1.2.3.4") == 30

    clock.now += 31  # the first failure is now over a minute old

    assert not throttle.is_refused("1.2.3.4")
    assert throttle.retry_after("1.2.3.4") == 0


def test_a_successful_login_clears_the_count() -> None:
    throttle, _ = throttle_with_clock()
    for _ in range(2):
        throttle.record_failure("1.2.3.4")

    throttle.reset("1.2.3.4")
    throttle.record_failure("1.2.3.4")

    assert not throttle.is_refused("1.2.3.4")


def test_checking_an_address_does_not_start_tracking_it() -> None:
    """Only failures take up memory, so ordinary logins leave nothing behind."""
    throttle, _ = throttle_with_clock()

    throttle.is_refused("1.2.3.4")
    throttle.retry_after("1.2.3.4")

    assert throttle._failures == {}
