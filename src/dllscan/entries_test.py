import struct
from collections.abc import Callable

import pytest

from .entries import CreationBase, decode_concommand, decode_creation_base
from .image import Image, read_image
from .image_fake import FakeSection, loaded
from .memory import Memory
from .shape import ShapeError

BASE = 0x180000000
RDATA = BASE + 0x1000
ENTRY = 0x10000000
"""Where the entry under test lives: on the heap, outside the image."""
STRAY = 0x20000000
"""A readable, printable string outside the image."""

type Decode = Callable[[Memory, int, Image], CreationBase]


class Fake:
    """An image at `BASE` whose `.rdata` holds strings, and one 64-byte entry
    `{name, help, flags, ...}` at `ENTRY`."""

    def __init__(self) -> None:
        self.rdata: bytearray = bytearray(8)

    def string(self, text: bytes) -> int:
        addr = RDATA + len(self.rdata)
        self.rdata += text + b"\0"
        return addr

    def load(self, name: int, help: int, flags: int, readable: int = 64) -> tuple[Memory, Image]:
        segments = loaded(BASE, [FakeSection(".rdata", RDATA - BASE, 0x40000040, bytes(self.rdata))])
        segments[STRAY] = b"sv_stray\0"
        segments[ENTRY] = struct.pack("<QQQ", name, help, flags).ljust(64, b"\xcc")[:readable]
        mem = Memory(segments)
        return mem, read_image(mem, BASE)


def decode(fake: Fake, name: int, help: int = 0, flags: int = 0, readable: int = 64) -> CreationBase:
    mem, image = fake.load(name, help, flags, readable)
    return decode_concommand(mem, ENTRY, image)


def misfit(fake: Fake, name: int, help: int = 0, readable: int = 64) -> tuple[object, ...]:
    """The `ShapeError`'s args: (what, entry address, ...)."""
    with pytest.raises(ShapeError) as raised:
        _ = decode(fake, name, help, readable=readable)
    return raised.value.args


class DescribeDecodeConcommand:
    @pytest.mark.parametrize("decoder", [decode_concommand, decode_creation_base])
    def it_decodes_name_help_and_flags(self, decoder: Decode):
        fake = Fake()
        name, help = fake.string(b"bot_kick_all"), fake.string(b"Kick all bots.")
        mem, image = fake.load(name, help, 0x2004000)
        assert decoder(mem, ENTRY, image) == {
            "name": "bot_kick_all",
            "help": "Kick all bots.",
            "flags": ("cheat", "client_can_execute"),
        }

    def it_reads_a_null_help_as_none(self):
        fake = Fake()
        assert decode(fake, fake.string(b"x"))["help"] is None

    def it_reads_an_empty_help_as_empty(self):
        fake = Fake()
        assert decode(fake, fake.string(b"x"), fake.string(b""))["help"] == ""

    def it_keeps_a_multiline_help(self):
        fake = Fake()
        assert decode(fake, fake.string(b"x"), fake.string(b"a\n\tb"))["help"] == "a\n\tb"

    def it_names_an_unknown_flag_bit_by_index(self):
        fake = Fake()
        assert decode(fake, fake.string(b"x"), flags=1 << 35 | 1 << 1)["flags"] == ("developmentonly", "flag_35")

    def it_reads_no_flags_as_none(self):
        fake = Fake()
        assert decode(fake, fake.string(b"x"))["flags"] == ()


class DescribeShapeErrors:
    @pytest.mark.parametrize("name", [b"", b"sv x", b"~" * 128, b"caf\xc3\xa9"])
    def it_rejects_a_name_that_breaks_the_rule(self, name: bytes):
        fake = Fake()
        assert misfit(fake, fake.string(name))[:2] == ("entry name", hex(ENTRY))

    @pytest.mark.parametrize("pointer", [0, STRAY, BASE - 8])
    def it_rejects_a_name_outside_the_image(self, pointer: int):
        assert misfit(Fake(), pointer)[:2] == ("entry name", hex(ENTRY))

    @pytest.mark.parametrize("pointer", [STRAY, BASE - 8, 1])
    def it_rejects_a_help_outside_the_image(self, pointer: int):
        fake = Fake()
        assert misfit(fake, fake.string(b"x"), pointer)[:2] == ("entry help", hex(ENTRY))

    def it_rejects_a_help_that_is_not_a_string(self):
        fake = Fake()
        assert misfit(fake, fake.string(b"x"), fake.string(b"\x01"))[:2] == ("entry help", hex(ENTRY))

    @pytest.mark.parametrize("readable", [0, 16, 23])
    def it_rejects_an_unreadable_entry(self, readable: int):
        fake = Fake()
        assert misfit(fake, fake.string(b"x"), readable=readable) == ("entry unreadable", hex(ENTRY))
