import struct
from collections.abc import Callable, Sequence

import pytest

from .document import ConVar
from .entries import CreationBase, decode_concommand, decode_convar, decode_creation_base
from .image import Image, read_image
from .image_fake import FakeSection, loaded
from .memory import Memory
from .shape import ShapeError
from .values import type_name

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

    def load(self, name: int, help: int, flags: int, readable: int | None = None, rest: bytes = b"\xcc" * 40) -> tuple[Memory, Image]:
        """`rest`: the entry past its base; a command's by default."""
        segments = loaded(BASE, [FakeSection(".rdata", RDATA - BASE, 0x40000040, bytes(self.rdata))])
        segments[STRAY] = b"sv_stray\0"
        segments[ENTRY] = (struct.pack("<QQQ", name, help, flags) + rest)[:readable]
        mem = Memory(segments)
        return mem, read_image(mem, BASE)


def decode(fake: Fake, name: int, help: int = 0, flags: int = 0, readable: int | None = None) -> CreationBase:
    mem, image = fake.load(name, help, flags, readable)
    return decode_concommand(mem, ENTRY, image)


def misfit(fake: Fake, name: int, help: int = 0, readable: int | None = None) -> tuple[object, ...]:
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


ABSENT = (bytes(16),) * 3
"""Three absent `CVValue_t`: all zero."""


def info(type: int, version: int = 0, has: tuple[int, int, int] = (0, 0, 0), values: Sequence[bytes] = ABSENT) -> bytes:
    """A convar entry past its base (`registration-flow.md`'s layout, less 24):
    version, has-bytes, three `CVValue_t`, then pointers and padding (stale
    `0xcc` here) around the type."""
    raw = bytearray(b"\xcc" * 136)
    struct.pack_into("<i3B", raw, 0, version, *has)
    raw[7:55] = b"".join(values)
    struct.pack_into("<h", raw, 96, type)
    return bytes(raw)


def f32(value: float) -> bytes:
    return struct.pack("<f", value).ljust(16, b"\0")


def convar(fake: Fake, rest: bytes, readable: int = 160) -> ConVar:
    mem, image = fake.load(fake.string(b"sv_x"), 0, 0, readable, rest)
    return decode_convar(mem, ENTRY, image)


def convar_misfit(fake: Fake, rest: bytes, readable: int = 160) -> tuple[object, ...]:
    with pytest.raises(ShapeError) as raised:
        _ = convar(fake, rest, readable)
    return raised.value.args


class DescribeDecodeConvar:
    def it_decodes_the_base_then_the_value_info(self):
        fake = Fake()
        name, help = fake.string(b"sv_gravity"), fake.string(b"World gravity.")
        rest = info(9, version=2, has=(1, 1, 1), values=(f32(800), f32(0.02), f32(4096)))
        mem, image = fake.load(name, help, 1 << 14 | 1 << 13, rest=rest)
        decoded = decode_convar(mem, ENTRY, image)
        assert list(decoded.items()) == [
            ("name", "sv_gravity"),
            ("help", "World gravity."),
            ("flags", ("replicated", "cheat")),
            ("type", "float32"),
            ("version", 2),
            ("default", 800.0),
            ("min", 0.02),
            ("max", 4096.0),
        ]

    def it_reads_each_slot_by_its_own_has_byte(self):
        decoded = convar(Fake(), info(5, has=(0, 1, 0), values=(bytes(16), (7).to_bytes(16, "little"), bytes(16))))
        assert (decoded["default"], decoded["min"], decoded["max"]) == (None, 7, None)

    def it_reads_a_reference_declaration_as_no_values(self):
        decoded = convar(Fake(), info(0))
        assert (decoded["type"], decoded["default"], decoded["min"], decoded["max"]) == ("bool", None, None, None)

    def it_reads_a_negative_version(self):
        assert convar(Fake(), info(0, version=-1))["version"] == -1

    def it_dereferences_a_string_default(self):
        decoded = convar(Fake(), info(11, has=(1, 0, 0), values=(STRAY.to_bytes(16, "little"), bytes(16), bytes(16))))
        assert decoded["default"] == "sv_stray"

    @pytest.mark.parametrize("code", range(18))
    def it_names_every_type(self, code: int):
        assert convar(Fake(), info(code))["type"] == type_name(code)


class DescribeConvarShapeErrors:
    @pytest.mark.parametrize("code", [-1, 18])
    def it_rejects_an_unknown_type(self, code: int):
        assert convar_misfit(Fake(), info(code)) == ("convar type", hex(ENTRY), code)

    def it_rejects_a_bad_value_with_the_entry_address(self):
        assert convar_misfit(Fake(), info(5, has=(0, 0, 2))) == ("convar has-byte", hex(ENTRY), 2)

    @pytest.mark.parametrize("readable", [64, 159])
    def it_rejects_an_entry_unreadable_past_its_base(self, readable: int):
        assert convar_misfit(Fake(), info(0), readable) == ("entry unreadable", hex(ENTRY))

    def it_rejects_a_bad_base(self):
        mem, image = Fake().load(STRAY, 0, 0, rest=info(0))
        with pytest.raises(ShapeError, match="entry name"):
            _ = decode_convar(mem, ENTRY, image)
