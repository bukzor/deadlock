"""A tiny seekable little-endian reader over an in-memory byte buffer.

Source 2 / VPK structures are little-endian and full of fixed-width integers
and NUL-terminated strings. This keeps the parsers declarative and the cursor
arithmetic in one well-tested place.
"""

from __future__ import annotations

import struct


class BinaryReader:
    def __init__(self, data: bytes, offset: int = 0) -> None:
        self._data = data
        self._pos = offset

    @property
    def pos(self) -> int:
        return self._pos

    def seek(self, pos: int) -> None:
        if pos < 0 or pos > len(self._data):
            raise ValueError(f"seek out of range: {pos} (len {len(self._data)})")
        self._pos = pos

    def skip(self, count: int) -> None:
        self.seek(self._pos + count)

    def eof(self) -> bool:
        return self._pos >= len(self._data)

    def read(self, count: int) -> bytes:
        end = self._pos + count
        if end > len(self._data):
            raise EOFError(f"read past end: want {count} at {self._pos}")
        chunk = self._data[self._pos : end]
        self._pos = end
        return chunk

    def _unpack(self, fmt: str) -> int:
        size = struct.calcsize(fmt)
        (value,) = struct.unpack_from(fmt, self._data, self._pos)
        self._pos += size
        return value

    def u8(self) -> int:
        return self._unpack("<B")

    def u16(self) -> int:
        return self._unpack("<H")

    def u32(self) -> int:
        return self._unpack("<I")

    def u64(self) -> int:
        return self._unpack("<Q")

    def i32(self) -> int:
        return self._unpack("<i")

    def cstring(self) -> str:
        """Read a NUL-terminated UTF-8 string, consuming the terminator.

        >>> r = BinaryReader(b"cfg\\x00panorama\\x00")
        >>> r.cstring()
        'cfg'
        >>> r.cstring()
        'panorama'
        """
        end = self._data.index(b"\x00", self._pos)
        chunk = self._data[self._pos : end]
        self._pos = end + 1
        return chunk.decode("utf-8")
