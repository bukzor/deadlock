import struct

import pytest

from .image import WRITE, Image, Section, read_image
from .image_fake import NT, OPT, TABLE, FakeSection, headers, loaded
from .memory import Memory, Segments
from .shape import ShapeError

BASE = 0x180000000
RDATA = 0x40000040
DATA = 0xC0000040
SECTIONS = [
    FakeSection(".rdata", 0x1000, RDATA, b"text", virtual_size=0x20),
    FakeSection(".data", 0x2000, DATA, b"data", virtual_size=0x30),
]
SIZE = 0x3000


def image_of(sections: list[FakeSection], size: int | None = None) -> Image:
    return read_image(Memory(loaded(BASE, sections, size)), BASE)


def patched(offset: int, fmt: str, value: object) -> Memory:
    """The `SECTIONS` headers at `BASE`, with one field overwritten."""
    raw = headers(SECTIONS, SIZE)
    struct.pack_into(fmt, raw, offset, value)
    return Memory(Segments({BASE: bytes(raw)}))


class DescribeReadImage:
    def it_reads_the_image_range(self):
        assert image_of(SECTIONS, SIZE).span == range(BASE, BASE + SIZE)

    def it_reads_each_section_in_table_order(self):
        assert image_of(SECTIONS, SIZE).sections == (
            Section(".rdata", range(BASE + 0x1000, BASE + 0x1020), RDATA),
            Section(".data", range(BASE + 0x2000, BASE + 0x2030), DATA),
        )

    def it_reads_headers_alone(self):
        assert read_image(patched(0, "<2s", b"MZ"), BASE) == image_of(SECTIONS, SIZE)

    def it_finds_the_section_table_after_the_optional_header(self):
        raw = headers(SECTIONS, SIZE)
        raw[TABLE:TABLE] = bytes(8)
        struct.pack_into("<H", raw, NT + 0x14, TABLE - OPT + 8)
        assert read_image(Memory(Segments({BASE: bytes(raw)})), BASE) == image_of(SECTIONS, SIZE)

    def it_keeps_a_full_eight_byte_name(self):
        (section,) = image_of([FakeSection(".textbss", 0x1000, RDATA, b"x")]).sections
        assert section.name == ".textbss"

    def it_spans_virtual_size_over_raw_size(self):
        (section,) = image_of([FakeSection(".data", 0x1000, DATA, virtual_size=0x10, raw_size=0x200)]).sections
        assert section.span == range(BASE + 0x1000, BASE + 0x1010)

    def it_falls_back_to_raw_size_when_virtual_size_is_zero(self):
        (section,) = image_of([FakeSection(".data", 0x1000, DATA, virtual_size=0, raw_size=0x200)]).sections
        assert section.span == range(BASE + 0x1000, BASE + 0x1200)

    def it_selects_the_writable_sections(self):
        image = image_of(SECTIONS, SIZE)
        assert [s.writable for s in image.sections] == [False, True]
        assert image.writable == (image.sections[1],)
        assert WRITE == 0x80000000


class DescribeMisfitHeaders:
    @pytest.mark.parametrize(
        ("offset", "fmt", "value"),
        [
            pytest.param(0, "<2s", b"ZM", id="no-MZ"),
            pytest.param(0x3C, "<I", 0x10000, id="PE-signature-unreadable"),
            pytest.param(NT, "<4s", b"PE\0\1", id="no-PE-signature"),
            pytest.param(NT + 4, "<H", 0x14C, id="i386"),
            pytest.param(OPT, "<H", 0x10B, id="PE32"),
            pytest.param(NT + 0x14, "<H", 0x6F, id="optional-header-too-small"),
            pytest.param(NT + 6, "<H", 3, id="section-table-unreadable"),
            pytest.param(OPT + 56, "<I", 0x2020, id="section-past-image-end"),
            pytest.param(TABLE, "<8s", b".da\x01ta", id="unprintable-name"),
            pytest.param(TABLE, "<8s", b"\xff", id="non-ascii-name"),
        ],
    )
    def it_raises_shape_error(self, offset: int, fmt: str, value: object):
        with pytest.raises(ShapeError):
            _ = read_image(patched(offset, fmt, value), BASE)

    def it_accepts_a_section_ending_at_the_image_end(self):
        assert read_image(patched(OPT + 56, "<I", 0x2030), BASE).span.stop == BASE + 0x2030

    @pytest.mark.parametrize(
        ("lo", "hi"),
        [
            pytest.param(0, TABLE + 80, id="everything"),
            pytest.param(0, 2, id="DOS-signature"),
            pytest.param(0x3C, 0x40, id="e_lfanew"),
        ],
    )
    def it_raises_when_a_field_is_unreadable(self, lo: int, hi: int):
        """The headers with `[lo, hi)` cut out."""
        raw = bytes(headers(SECTIONS, SIZE))
        with pytest.raises(ShapeError):
            _ = read_image(Memory(Segments({BASE: raw[:lo], BASE + hi: raw[hi:]})), BASE)
