import json
import struct

import pytest

from .facets import concommands, convars, dumps, load_failed, load_ok
from .reglist import STRIDES
from .reglist_fake import Fake, logged
from .shape import ShapeError
from .win32 import Win32Error

CONVAR, COMMAND = STRIDES["convars"], STRIDES["concommands"]
DLL = "C:\\Steam\\Game\\Citadel\\BIN\\Server.DLL"


def names(fake: Fake, prefix: bytes, n: int):
    """`n` entries named `<prefix><i>`."""
    return [fake.entry(b"%s%d" % (prefix, i)) for i in range(n)]


class DescribeLoadOk:
    def it_records_only_the_modules_the_load_added_sorted(self):
        before = ["python312.dll", "kernel32.dll", "_ctypes.pyd"]
        after = [*before, "tier0.dll", "server.dll", "steam_api64.dll"]
        assert load_ok(before, after) == {"outcome": "ok", "modules": ["server.dll", "steam_api64.dll", "tier0.dll"]}


class DescribeLoadFailed:
    def it_records_the_function_and_code_but_not_the_path(self):
        error = Win32Error("LoadLibraryExW", 126, "C:\\Steam\\vfx_dx11.dll")
        assert load_failed(error) == {"outcome": "failed", "error": "LoadLibraryExW: 126"}


class DescribeConcommands:
    def it_decodes_the_command_queue_in_order(self):
        fake = Fake()
        _, convar_blocks = fake.queue(CONVAR, names(fake, b"cv", 3))
        _, blocks = fake.queue(COMMAND, [fake.entry(b"b"), fake.entry(b"a", b"some help"), fake.entry(b"c")])
        mem, image = fake.load()
        assert concommands(mem, image, DLL, logged("convars", convar_blocks) + logged("concommands", blocks)) == {
            "dll": "Server.DLL",
            "concommands": [
                {"name": "b", "help": None, "flags": ()},
                {"name": "a", "help": "some help", "flags": ()},
                {"name": "c", "help": None, "flags": ()},
            ],
        }

    def it_is_empty_without_a_command_queue(self):
        fake = Fake()
        _, blocks = fake.queue(CONVAR, names(fake, b"cv", 3))
        mem, image = fake.load()
        assert concommands(mem, image, "x.dll", logged("convars", blocks)) == {"dll": "x.dll", "concommands": []}

    def it_raises_when_the_log_and_the_queue_disagree(self):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, names(fake, b"a", 1))
        fake.data[-8:] = bytes(8)  # the head slot
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="concommands head slots"):
            _ = concommands(mem, image, DLL, logged("concommands", blocks))

    class WhenTier0:
        def it_scans_for_the_queue_without_a_log(self):
            fake = Fake()
            _ = fake.queue(COMMAND, [fake.entry(b"find")])
            mem, image = fake.load()
            assert concommands(mem, image, DLL, None)["concommands"] == [{"name": "find", "help": None, "flags": ()}]

        def it_raises_on_a_second_command_queue(self):
            fake = Fake()
            _ = fake.queue(COMMAND, names(fake, b"a", 1))
            _ = fake.queue(COMMAND, names(fake, b"b", 2))
            mem, image = fake.load()
            with pytest.raises(ShapeError, match="more than one concommands queue"):
                _ = concommands(mem, image, DLL, None)


ABSENT = {"type": "bool", "version": 0, "default": None, "min": None, "max": None}
"""An all-zero convar entry's value info: a bool with no values."""


class DescribeConvars:
    def it_decodes_the_convar_queue_in_order(self):
        fake = Fake()
        _ = fake.queue(COMMAND, names(fake, b"cc", 2))
        _, (block,) = fake.queue(CONVAR, [fake.entry(b"b"), fake.entry(b"a", b"some help"), fake.entry(b"c")])
        second = block + 8 + CONVAR
        fake.poke(second + 24, "<i", 3)
        fake.poke(second + 28, "<B", 1)
        fake.poke(second + 31, "<I", int.from_bytes(struct.pack("<f", 0.25), "little"))
        fake.poke(second + 120, "<h", 9)
        mem, image = fake.load()
        assert convars(mem, image, DLL, logged("convars", [block])) == {
            "dll": "Server.DLL",
            "convars": [
                {"name": "b", "help": None, "flags": (), **ABSENT},
                {"name": "a", "help": "some help", "flags": (), **ABSENT, "type": "float32", "version": 3, "default": 0.25},
                {"name": "c", "help": None, "flags": (), **ABSENT},
            ],
        }

    def it_is_empty_without_a_convar_queue(self):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, names(fake, b"cc", 2))
        mem, image = fake.load()
        assert convars(mem, image, "x.dll", logged("concommands", blocks)) == {"dll": "x.dll", "convars": []}

    def it_raises_on_a_second_convar_queue_without_a_log(self):
        fake = Fake()
        _ = fake.queue(CONVAR, names(fake, b"a", 1))
        _ = fake.queue(CONVAR, names(fake, b"b", 2))
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="more than one convars queue"):
            _ = convars(mem, image, DLL, None)


class DescribeDumps:
    def it_keeps_key_order_and_unicode_one_value_per_line(self):
        text = dumps({"dll": "x.dll", "concommands": [{"name": "a", "help": "café", "flags": ("cheat",)}]})
        assert text == (
            '{\n  "dll": "x.dll",\n  "concommands": [\n    {\n      "name": "a",\n'
            '      "help": "café",\n      "flags": [\n        "cheat"\n      ]\n    }\n  ]\n}\n'
        )
        assert json.loads(text)["concommands"][0]["help"] == "café"
