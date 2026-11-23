"""Test helpers shared by the damage model's tests."""

import signal
from collections.abc import Generator
from contextlib import contextmanager


@contextmanager
def within(seconds: int) -> Generator[None]:
    """Fail, rather than hang the run, if the block takes more than ``seconds`` (Unix main thread)."""

    def expired(_signum: int, _frame: object) -> None:
        raise TimeoutError(f"still running after {seconds} s: an unbounded loop?")

    previous = signal.signal(signal.SIGALRM, expired)
    _ = signal.alarm(seconds)
    try:
        yield
    finally:
        _ = signal.alarm(0)
        _ = signal.signal(signal.SIGALRM, previous)
