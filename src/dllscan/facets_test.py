import json

import pytest

from .facets import ANCHORS, concommands, dumps, load_failed, load_ok, strides
from .reglist import BLOCK, STRIDES
from .reglist_fake import Fake
from .shape import ShapeError
from .win32 import Win32Error

CONVAR, COMMAND = STRIDES["convars"], STRIDES["concommands"]
DLL = "C:\\Steam\\Game\\Citadel\\BIN\\Server.DLL"
LANE_SWAP = b"citadel_lane_swap_available_duration_prematch"


def names(fake: Fake, prefix: bytes, n: int, anchor: bytes | None = None):
    """`n` entries named `<prefix><i>`, the last one named `anchor` if given."""
    entries = [fake.entry(b"%s%d" % (prefix, i)) for i in range(n)]
    if anchor is not None:
        entries[-1] = fake.entry(anchor)
    return entries


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
        _ = fake.queue(CONVAR, names(fake, b"cv", 3))
        _ = fake.queue(COMMAND, [fake.entry(b"b"), fake.entry(b"a", b"some help"), fake.entry(b"c")])
        mem, image = fake.load()
        assert concommands(mem, image, DLL) == {
            "module": "Server.DLL",
            "concommands": [
                {"name": "b", "help": None, "flags": ()},
                {"name": "a", "help": "some help", "flags": ()},
                {"name": "c", "help": None, "flags": ()},
            ],
        }

    def it_is_empty_without_a_command_queue(self):
        fake = Fake()
        _ = fake.queue(CONVAR, names(fake, b"cv", 3))
        mem, image = fake.load()
        assert concommands(mem, image, "x.dll") == {"module": "x.dll", "concommands": []}

    def it_raises_on_a_second_command_queue(self):
        fake = Fake()
        _ = fake.queue(COMMAND, names(fake, b"a", 1))
        _ = fake.queue(COMMAND, names(fake, b"b", 2))
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="concommands"):
            _ = concommands(mem, image, DLL)


class DescribeStrides:
    def it_labels_the_pinned_strides_by_their_anchors(self):
        fake = Fake()
        _ = fake.queue(CONVAR, names(fake, b"cv", BLOCK + 2, LANE_SWAP))
        _ = fake.queue(COMMAND, names(fake, b"cc", BLOCK + 1, b"bot_kick_all"))
        mem, image = fake.load()
        assert strides(mem, image) == [
            {"stride": CONVAR, "kind": "convars", "entries": BLOCK + 2},
            {"stride": COMMAND, "kind": "concommands", "entries": BLOCK + 1},
        ]

    def it_leaves_a_queue_without_anchors_unlabelled(self):
        fake = Fake()
        _ = fake.queue(COMMAND, names(fake, b"cc", BLOCK + 1, b"citadel_bot_kick"))
        _ = fake.queue(CONVAR, names(fake, b"cv", BLOCK + 1))
        mem, image = fake.load()
        assert [learned["kind"] for learned in strides(mem, image)] == ["concommands", None]

    def it_raises_when_a_stride_moved(self):
        fake = Fake()
        _ = fake.queue(CONVAR + 8, names(fake, b"cv", BLOCK + 1))
        _ = fake.queue(COMMAND, names(fake, b"cc", BLOCK + 1))
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="strides moved"):
            _ = strides(mem, image)

    def it_raises_when_a_queue_is_missing(self):
        fake = Fake()
        _ = fake.queue(CONVAR, names(fake, b"cv", BLOCK + 1))
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="strides moved"):
            _ = strides(mem, image)

    def it_raises_on_an_anchor_in_the_wrong_queue(self):
        fake = Fake()
        _ = fake.queue(CONVAR, names(fake, b"cv", BLOCK + 1, b"bot_kick_all"))
        _ = fake.queue(COMMAND, names(fake, b"cc", BLOCK + 1))
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="anchor"):
            _ = strides(mem, image)

    def it_raises_on_a_queue_with_anchors_of_both_kinds(self):
        fake = Fake()
        _ = fake.queue(CONVAR, [*names(fake, b"cv", BLOCK, LANE_SWAP), fake.entry(b"find")])
        _ = fake.queue(COMMAND, names(fake, b"cc", BLOCK + 1))
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="anchors of both kinds"):
            _ = strides(mem, image)

    def it_anchors_the_names_validation_lists(self):
        assert ANCHORS == {
            "bot_kick_all": "concommands",
            "citadel_bot_kick": "concommands",
            "find": "concommands",
            "citadel_lane_swap_available_duration_prematch": "convars",
        }


class DescribeDumps:
    def it_keeps_key_order_and_unicode_one_value_per_line(self):
        text = dumps({"module": "x.dll", "concommands": [{"name": "a", "help": "café", "flags": ("cheat",)}]})
        assert text == (
            '{\n  "module": "x.dll",\n  "concommands": [\n    {\n      "name": "a",\n'
            '      "help": "café",\n      "flags": [\n        "cheat"\n      ]\n    }\n  ]\n}\n'
        )
        assert json.loads(text)["concommands"][0]["help"] == "café"
