import struct

import pytest

from .binary import BinaryReader


class DescribeBinaryReader:
    def it_reads_fixed_width_little_endian_integers(self):
        data = struct.pack("<BHIQ", 1, 2, 3, 4)
        r = BinaryReader(data)
        assert r.u8() == 1
        assert r.u16() == 2
        assert r.u32() == 3
        assert r.u64() == 4
        assert r.eof()

    def it_reads_signed_int32(self):
        r = BinaryReader(struct.pack("<i", -5))
        assert r.i32() == -5

    def it_reads_nul_terminated_strings_and_consumes_terminator(self):
        r = BinaryReader(b"abc\x00def\x00")
        assert r.cstring() == "abc"
        assert r.pos == 4
        assert r.cstring() == "def"

    def it_reads_an_empty_cstring(self):
        r = BinaryReader(b"\x00rest")
        assert r.cstring() == ""
        assert r.pos == 1

    def it_seeks_and_skips(self):
        r = BinaryReader(b"0123456789")
        r.seek(4)
        assert r.read(2) == b"45"
        r.skip(1)
        assert r.read(1) == b"7"

    def it_raises_on_read_past_end(self):
        r = BinaryReader(b"ab")
        with pytest.raises(EOFError):
            r.read(3)

    def it_raises_on_out_of_range_seek(self):
        r = BinaryReader(b"ab")
        with pytest.raises(ValueError):
            r.seek(99)
