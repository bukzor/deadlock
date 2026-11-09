import struct

from .memory import MAX_CSTR, PAGE, Memory, Segments


def mem(segments: dict[int, bytes]) -> Memory:
    return Memory(Segments(segments))


class DescribeSegments:
    def it_reads_inside_one_segment(self):
        read = Segments({0x1000: b"abcdef"})
        assert read(0x1001, 3) == b"bcd"
        assert read(0x1000, 6) == b"abcdef"

    def it_refuses_a_read_outside_every_segment(self):
        read = Segments({0x1000: b"abcdef"})
        assert read(0xFFF, 1) is None
        assert read(0x1006, 1) is None

    def it_refuses_a_read_past_a_segment_end(self):
        assert Segments({0x1000: b"abcdef"})(0x1004, 3) is None

    def it_refuses_a_read_straddling_adjacent_segments(self):
        read = Segments({0x1000: b"abc", 0x1003: b"def"})
        assert read(0x1003, 3) == b"def"
        assert read(0x1002, 2) is None


class DescribeMemory:
    class WhenReadingIntegers:
        def it_reads_little_endian(self):
            m = mem({0x1000: struct.pack("<HIQ", 0x0102, 0x03040506, 0x0708090A0B0C0D0E)})
            assert m.u16(0x1000) == 0x0102
            assert m.u32(0x1002) == 0x03040506
            assert m.u64(0x1006) == 0x0708090A0B0C0D0E

        def it_returns_none_when_unreadable(self):
            m = mem({0x1000: bytes(8)})
            assert m.u16(0x1007) is None
            assert m.u32(0x1005) is None
            assert m.u64(0x1001) is None

    class WhenReadingCstr:
        def it_reads_the_string_before_the_nul(self):
            m = mem({0x1000: b"name\0junk"})
            assert m.cstr_in(0x1000, 0x1000, 0x1009) == "name"

        def it_reads_help_text(self):
            m = mem({0x1000: "Sets a\tthing.\r\nMore: 5°\0".encode()})
            assert m.cstr_in(0x1000, 0x1000, 0x1100) == "Sets a\tthing.\r\nMore: 5°"

        def it_reads_an_empty_string(self):
            assert mem({0x1000: b"\0"}).cstr_in(0x1000, 0x1000, 0x1001) == ""

        def it_refuses_an_address_outside_the_range(self):
            m = mem({0x1000: b"a\0b\0"})
            assert m.cstr_in(0x1000, 0x1001, 0x1004) is None
            assert m.cstr_in(0x1002, 0x1000, 0x1002) is None

        def it_accepts_a_nul_on_the_last_byte_of_the_range(self):
            assert mem({0x1000: b"abc\0"}).cstr_in(0x1000, 0x1000, 0x1004) == "abc"

        def it_refuses_a_nul_past_the_range(self):
            assert mem({0x1000: b"abc\0"}).cstr_in(0x1000, 0x1000, 0x1003) is None

        def it_refuses_a_nonprintable_byte(self):
            assert mem({0x1000: b"ab\x01c\0"}).cstr_in(0x1000, 0x1000, 0x1100) is None

        def it_refuses_invalid_utf8(self):
            assert mem({0x1000: b"ab\xffc\0"}).cstr_in(0x1000, 0x1000, 0x1100) is None

        def it_refuses_an_unreadable_byte_before_the_nul(self):
            assert mem({0x1000: b"abc"}).cstr_in(0x1000, 0x1000, 0x1100) is None

        def it_reads_across_a_page_boundary(self):
            text = b"x" * 10 + b"y" * 10
            m = mem({PAGE - 10: text + b"\0"})
            assert m.cstr_in(PAGE - 10, 0, 2 * PAGE) == text.decode()

        def it_reads_up_to_a_segment_end_off_the_page_grid(self):
            m = mem({0x1000: b"zz", 0x1010: b"abc\0"})
            assert m.cstr_in(0x1010, 0x1000, 0x2000) == "abc"

        def it_accepts_max_cstr_bytes(self):
            text = b"a" * MAX_CSTR
            assert mem({0x1000: text + b"\0"}).cstr_in(0x1000, 0, 1 << 20) == text.decode()

        def it_refuses_longer_strings(self):
            text = b"a" * (MAX_CSTR + 1)
            assert mem({0x1000: text + b"\0"}).cstr_in(0x1000, 0, 1 << 20) is None
