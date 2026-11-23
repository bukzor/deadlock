import struct

import pytest

from .document import ConVarValue
from .memory import Memory, Segments
from .shape import ShapeError
from .values import TYPES, decode, type_name

HEAP = 0x10000000
"""Where a string value's `char*` points."""
MEM = Memory(Segments({HEAP: b"text\0", HEAP + 8: b"\0", HEAP + 16: b"\x01\0"}))


def value(fmt: str, *fields: object) -> bytes:
    """A `CVValue_t`: the fields packed little-endian, zero-padded to 16 bytes."""
    return struct.pack("<" + fmt, *fields).ljust(16, b"\0")


def misfit(type: str, has: int, raw: bytes) -> tuple[object, ...]:
    with pytest.raises(ShapeError) as raised:
        _ = decode(MEM, type, has, raw)
    return raised.value.args


class DescribeTypeName:
    def it_reads_the_binarys_table_by_code(self):
        assert [type_name(code) for code in range(18)] == [
            "bool", "int8", "uint8", "int16", "uint16", "int32", "uint32", "int64", "uint64",
            "float32", "float64", "string", "color", "vector2", "vector3", "vector4", "qangle", "vectorws",
        ]  # fmt: skip

    def it_sizes_each_type_as_the_binary_does(self):
        assert list(TYPES.values()) == [1, 1, 1, 2, 2, 4, 4, 8, 8, 4, 8, 8, 4, 8, 12, 16, 12, 12]

    @pytest.mark.parametrize("code", [-1, 18, 0x7FFF])
    def it_rejects_an_unknown_code(self, code: int):
        with pytest.raises(ShapeError) as raised:
            _ = type_name(code)
        assert raised.value.args == ("convar type", code)


class DescribeDecode:
    @pytest.mark.parametrize(
        ("type", "raw", "expected"),
        [
            ("bool", value("B", 0), False),
            ("bool", value("B", 1), True),
            ("int8", value("b", -2), -2),
            ("uint8", value("B", 254), 254),
            ("int16", value("h", -300), -300),
            ("uint16", value("H", 65000), 65000),
            ("int32", value("i", -70000), -70000),
            ("uint32", value("I", 4000000000), 4000000000),
            ("int64", value("q", -(1 << 40)), -(1 << 40)),
            ("uint64", value("Q", (1 << 64) - 1), (1 << 64) - 1),
            ("float32", value("f", 0.02), 0.02),
            ("float32", value("f", -0.0), -0.0),
            ("float32", value("f", 3.4028234663852886e38), 3.4028235e38),
            ("float64", value("d", 0.1), 0.1),
            ("string", value("Q", HEAP), "text"),
            ("string", value("Q", HEAP + 8), ""),
            ("string", value("Q", 0), ""),
            ("color", value("4B", 255, 128, 0, 7), [255, 128, 0, 7]),
            ("vector2", value("2f", 0.5, -1.1), [0.5, -1.1]),
            ("vector3", value("3f", 1, 2, 0.3), [1.0, 2.0, 0.3]),
            ("vector4", value("4f", 1, 2, 3, 0.4), [1.0, 2.0, 3.0, 0.4]),
            ("qangle", value("3f", 90, -45.5, 0.1), [90.0, -45.5, 0.1]),
            ("vectorws", value("3f", 0.7, 8, 9), [0.7, 8.0, 9.0]),
        ],
    )
    def it_decodes_a_present_value_by_type(self, type: str, raw: bytes, expected: ConVarValue):
        decoded = decode(MEM, type, 1, raw)
        assert (decoded, repr(decoded)) == (expected, repr(expected))

    @pytest.mark.parametrize("type", list(TYPES))
    def it_reads_an_absent_value_as_none(self, type: str):
        assert decode(MEM, type, 0, bytes(16)) is None


class DescribeShapeErrors:
    @pytest.mark.parametrize("has", [2, 0xFF])
    def it_rejects_a_has_byte_other_than_0_or_1(self, has: int):
        assert misfit("int32", has, bytes(16)) == ("convar has-byte", has)

    @pytest.mark.parametrize("raw", [b"\1" + bytes(15), bytes(15) + b"\1"])
    def it_rejects_an_absent_value_that_is_not_zero(self, raw: bytes):
        assert misfit("int32", 0, raw) == ("convar absent value", raw.hex())

    @pytest.mark.parametrize(("type", "size"), [("bool", 1), ("int32", 4), ("string", 8), ("vector3", 12)])
    def it_rejects_a_present_value_with_bytes_past_its_size(self, type: str, size: int):
        raw = bytes(size) + b"\1" + bytes(15 - size)
        assert misfit(type, 1, raw) == ("convar value tail", type, raw.hex())

    def it_rejects_a_bool_other_than_0_or_1(self):
        assert misfit("bool", 1, value("B", 2)) == ("convar bool", value("B", 2).hex())

    @pytest.mark.parametrize("pointer", [HEAP + 16, HEAP + 1024, 8])
    def it_rejects_a_string_pointer_that_is_not_a_string(self, pointer: int):
        assert misfit("string", 1, value("Q", pointer)) == ("convar string", hex(pointer))

    @pytest.mark.parametrize(
        ("type", "raw"),
        [
            ("float32", value("f", float("inf"))),
            ("float64", value("d", float("nan"))),
            ("vector3", value("3f", 0, float("-inf"), 0)),
        ],
    )
    def it_rejects_a_float_that_json_cannot_hold(self, type: str, raw: bytes):
        assert misfit(type, 1, raw)[:2] == ("convar float", type)
