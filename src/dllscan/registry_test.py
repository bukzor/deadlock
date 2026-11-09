import struct

import pytest

from .memory import Memory, Segments
from .registry import BLOCK, OBJECT, OBJECTS, SLOTS, MAX_INDEX, Placeholders, block, command_record, convar_record, walk
from .shape import ShapeError

BASE = 0x7000_0000
DATA = 0x1000
"""Where a fake `ConVarData` / `ConCommandData` sits."""
TEXT = 0x2000
VALUES = 0x3000
UNMAPPED = 0x9000
QUARTER = struct.pack("<f", 0.25)


def _u64(raw: bytes, at: int) -> int:
    return int.from_bytes(raw[at : at + 8], "little")


class DescribeBlock:
    def it_points_every_slot_at_one_stub_that_reads_the_mode_from_the_block(self):
        raw = block(BASE)
        stub = _u64(raw, 128)
        assert [_u64(raw, 128 + 8 * i) for i in range(SLOTS)] == [stub] * SLOTS
        code = raw[stub - BASE :]
        assert code[:2] == b"\x49\xbb" and _u64(code, 2) == BASE  # mov r11, base
        assert b"\x0f\x0b" in code[:32]  # ud2

    def it_starts_with_a_zero_trap_cell_and_mode(self):
        assert block(BASE)[:24] == bytes(24)

    def it_lays_out_objects_that_each_lead_with_the_vtable_pointer(self):
        raw = block(BASE)
        assert len(raw) == BLOCK
        pool = raw[BLOCK - OBJECT * OBJECTS :]
        vtable = (BASE + 128).to_bytes(8, "little")
        assert {pool[i : i + OBJECT] for i in range(0, len(pool), OBJECT)} == {vtable.ljust(OBJECT, b"\0")}


class DescribePlaceholders:
    def it_gives_each_name_its_own_object_in_the_pool(self):
        ph = Placeholders(BASE)
        a, b = ph.make("A001"), ph.make("B001")
        assert (a, b) == (BASE + BLOCK - OBJECT * OBJECTS, BASE + BLOCK - OBJECT * (OBJECTS - 1))
        assert ph.make("A001") == a

    def it_puts_the_mode_after_the_trap_cell(self):
        assert Placeholders(BASE).mode == BASE + 16

    def it_runs_out_after_the_pool(self):
        ph = Placeholders(BASE)
        for i in range(OBJECTS):
            _ = ph.make(f"I{i}")
        with pytest.raises(AssertionError):
            _ = ph.make("one more")

    def it_names_the_placeholder_that_trapped(self):
        ph = Placeholders(BASE)
        _, b = ph.make("A001"), ph.make("B001")
        assert ph.tripped(Memory(Segments({BASE: b.to_bytes(8, "little")}))) == "B001"

    def it_reads_no_trap_as_none(self):
        assert Placeholders(BASE).tripped(Memory(Segments({BASE: bytes(8)}))) is None

    def it_rejects_a_trap_by_no_placeholder(self):
        with pytest.raises(AssertionError):
            _ = Placeholders(BASE).tripped(Memory(Segments({BASE: (BASE + 8).to_bytes(8, "little")})))


def _convar_data(type: int = 9, default: int = VALUES, min: int = 0, help: int = TEXT + 5, version: int = 0) -> bytes:
    """A `ConVarData` up to its flags (`gamedll cheat`); no max."""
    return struct.pack("<5QhhIQ", TEXT, default, min, 0, help, type, version, 0, 1 << 14 | 1 << 2)


def _mem(data: bytes, value: bytes = QUARTER) -> Memory:
    """`data` at `DATA`, "name" and "help" at `TEXT`, `value` at `VALUES`."""
    return Memory(Segments({DATA: data, TEXT: b"name\0help\0", VALUES: value}))


class DescribeConvarRecord:
    def it_reads_a_convar_data_as_a_queue_entry(self):
        assert convar_record(_mem(_convar_data(version=-1)), DATA) == {
            "name": "name",
            "help": "help",
            "flags": ("gamedll", "cheat"),
            "type": "float32",
            "version": -1,
            "default": 0.25,
            "min": None,
            "max": None,
        }

    def it_reads_only_the_types_size_of_a_value(self):
        mem = _mem(_convar_data(type=0, min=VALUES), b"\1" + b"\xcb" * 15)
        record = convar_record(mem, DATA)
        assert (record["type"], record["default"], record["min"]) == ("bool", True, True)

    def it_reads_a_string_through_its_pointer(self):
        mem = _mem(_convar_data(type=11), TEXT.to_bytes(8, "little"))
        assert convar_record(mem, DATA)["default"] == "name"

    def it_reads_null_help_as_none(self):
        assert convar_record(_mem(_convar_data(help=0)), DATA)["help"] is None

    @pytest.mark.parametrize(
        ("data", "what"),
        [
            (_convar_data()[:-1], "registry record unreadable"),
            (_convar_data(type=18), "registry convar type"),
            (_convar_data(default=VALUES + 8), "registry value unreadable"),
            (_convar_data(help=UNMAPPED), "registry help"),
            (b"\0" * 8 + _convar_data()[8:], "registry name"),
        ],
        ids=["unreadable", "type", "value", "help", "name"],
    )
    def it_raises_on_a_misfit_naming_the_record(self, data: bytes, what: str):
        with pytest.raises(ShapeError) as raised:
            _ = convar_record(_mem(data), DATA)
        assert raised.value.args[:2] == (what, hex(DATA))

    def it_raises_on_a_value_that_misfits_its_type(self):
        with pytest.raises(ShapeError) as raised:
            _ = convar_record(_mem(_convar_data(type=0), b"\2"), DATA)
        assert raised.value.args[:2] == ("registry convar bool", hex(DATA))


class DescribeCommandRecord:
    def it_reads_a_concommand_data_as_a_queue_entry(self):
        mem = _mem(struct.pack("<3Q", TEXT, 0, 1 << 2))
        assert command_record(mem, DATA) == {"name": "name", "help": None, "flags": ("gamedll",)}

    def it_raises_on_a_misfit_naming_the_record(self):
        with pytest.raises(ShapeError) as raised:
            _ = command_record(_mem(struct.pack("<3Q", TEXT, UNMAPPED, 0)), DATA)
        assert raised.value.args[:2] == ("registry help", hex(DATA))


class DescribeWalk:
    def it_stops_at_null(self):
        assert walk(lambda i: [7, 8, 0, 9][i] if i < 4 else 0) == [7, 8]

    def it_stops_at_what_the_invalid_index_gets(self):
        assert walk(lambda i: 5 if i == MAX_INDEX else [7, 8, 5, 9][i]) == [7, 8]

    def it_fails_without_an_end(self):
        with pytest.raises(AssertionError):
            _ = walk(lambda i: 0 if i == MAX_INDEX else i + 1)
