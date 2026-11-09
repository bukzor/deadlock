"""Typed reads of a process's memory through a `Read` callable.

The scanner guesses at layouts, so most addresses it tries are wrong. A wrong
guess must read as "doesn't fit", never crash: every read here returns None
when any byte of it is unreadable, and callers treat None as a misfit.

>>> mem = Memory(Segments({0x1000: b"\\x2a\\0\\0\\0name\\0"}))
>>> mem.u32(0x1000), mem.cstr_in(0x1004, 0x1000, 0x1009)
(42, 'name')
>>> mem.u64(0x1004) is None, mem.cstr_in(0x1004, 0x1000, 0x1008) is None
(True, True)
"""

from collections.abc import Callable

type Read = Callable[[int, int], bytes | None]
"""`read(addr, n)`: the `n` bytes at `addr`, or None if any is unreadable.
Never raises for a bad address."""

MAX_CSTR = 4096
"""Longest string `cstr_in` accepts, in bytes before the NUL. Help text runs to
hundreds of bytes; a run past this is not a string we want, so it reads as None."""

PAGE = 4096
"""Readability granule of real memory: `cstr_in` reads at most up to the next
multiple of this per call, so one read never spans a readable and an unreadable page."""


class Segments(dict[int, bytes]):
    """A test fake: `{base: data}`, callable as a `Read`. A read is satisfied
    only if it lies entirely inside one segment; adjacency doesn't join them."""

    def __call__(self, addr: int, n: int) -> bytes | None:
        for base, data in self.items():
            if base <= addr and addr + n <= base + len(data):
                return data[addr - base : addr - base + n]
        return None


class Memory:
    """Little-endian integer and string reads over a `Read`."""

    def __init__(self, read: Read) -> None:
        self.read: Read = read

    def _uint(self, addr: int, size: int) -> int | None:
        data = self.read(addr, size)
        return None if data is None else int.from_bytes(data, "little")

    def u16(self, addr: int) -> int | None:
        """The u16 at `addr`, or None if unreadable."""
        return self._uint(addr, 2)

    def u32(self, addr: int) -> int | None:
        """The u32 at `addr`, or None if unreadable."""
        return self._uint(addr, 4)

    def u64(self, addr: int) -> int | None:
        """The u64 at `addr`, or None if unreadable."""
        return self._uint(addr, 8)

    def cstr_in(self, addr: int, lo: int, hi: int) -> str | None:
        """The NUL-terminated printable string at `addr`, else None.

        None unless `lo <= addr < hi` and the string and its NUL lie inside
        `[lo, hi)`, readable, within `MAX_CSTR` bytes. Printable: strict UTF-8,
        every char `isprintable()` or one of `\\t\\r\\n`; empty is allowed. A
        name's stricter shape (non-empty, no spaces) is the caller's to check.
        """
        if not lo <= addr < hi:
            return None
        raw = self._until_nul(addr, min(hi, addr + MAX_CSTR + 1))
        if raw is None:
            return None
        try:
            text = raw.decode()
        except UnicodeDecodeError:
            return None
        return text if all(c.isprintable() or c in "\t\r\n" for c in text) else None

    def _until_nul(self, addr: int, end: int) -> bytes | None:
        """The bytes from `addr` up to a NUL before `end`, or None."""
        out = bytearray()
        at = addr
        while at < end:
            chunk = self._chunk(at, min(end, (at // PAGE + 1) * PAGE))
            if chunk is None:
                return None
            nul = chunk.find(0)
            if nul >= 0:
                return bytes(out + chunk[:nul])
            out += chunk
            at += len(chunk)
        return None

    def _chunk(self, at: int, end: int) -> bytes | None:
        """`[at, end)` in one read, or else just the byte at `at`, or None."""
        return self.read(at, end - at) or self.read(at, 1)
