"""Refuse admin logins from an address that keeps getting the password wrong."""

import time
from collections import deque
from collections.abc import Callable

MAX_FAILURES = 5
WINDOW_SECONDS = 15 * 60

# Past this many tracked addresses, the next failure first forgets the ones
# whose failures have all expired, so a scan from many addresses can't grow
# the table without limit.
SWEEP_ABOVE = 10_000


class LoginThrottle:
    """Counts failed logins per client address, over a sliding window.

    After MAX_FAILURES failures inside WINDOW_SECONDS, that address is refused,
    even with the right password, until its oldest failure ages out of the
    window. Per address rather than per account: the admin has only two
    accounts, and locking an account would let any stranger lock its owner out
    by typing wrong passwords on purpose.

    The counts live in memory. That's enough for one server: a restart, which
    every deploy causes, clears them, and several servers would each keep their
    own. Shared counts would need a store such as Redis.

    The clock is a parameter so tests can move time forward instead of
    waiting. time.monotonic, because it never jumps when the system clock is
    adjusted.

    Not thread-safe, and doesn't need to be: the login handler is async, so
    every call happens on the event loop's one thread.
    """

    def __init__(
        self,
        max_failures: int = MAX_FAILURES,
        window_seconds: float = WINDOW_SECONDS,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self.clock = clock
        self._failures: dict[str, deque[float]] = {}

    def is_refused(self, address: str) -> bool:
        return len(self._recent(address)) >= self.max_failures

    def retry_after(self, address: str) -> int:
        """Whole seconds until the address may try again; 0 if it may now."""
        recent = self._recent(address)
        if len(recent) < self.max_failures:
            return 0
        # The address is let back in once enough of its failures expire to
        # bring it under the limit.
        unblocks_at = recent[len(recent) - self.max_failures] + self.window_seconds
        return max(1, int(unblocks_at - self.clock() + 0.999))

    def record_failure(self, address: str) -> None:
        if len(self._failures) > SWEEP_ABOVE:
            self._sweep()
        # Drop the expired failures first, so a slow, steady guesser's list
        # stays at most MAX_FAILURES long.
        self._recent(address)
        self._failures.setdefault(address, deque()).append(self.clock())

    def reset(self, address: str) -> None:
        """Forget an address's failures, after it signs in successfully."""
        self._failures.pop(address, None)

    def _recent(self, address: str) -> deque[float]:
        """The address's failures still inside the window, oldest first."""
        failures = self._failures.get(address, deque())
        cutoff = self.clock() - self.window_seconds
        while failures and failures[0] <= cutoff:
            failures.popleft()
        return failures

    def _sweep(self) -> None:
        for address in list(self._failures):
            if not self._recent(address):
                del self._failures[address]
