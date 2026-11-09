import struct

import pytest

from .memory import Memory
from .reglist import BLOCK, REF_TESTS, STRIDES, UNREGISTERED, Queue, RefTest, find_queues, learn_strides, name_at, owned_ref
from .reglist import unregistered_command_ref, walk
from .reglist_fake import DATA, HEAP, RDATA, Fake
from .shape import ShapeError

CONVAR, COMMAND = STRIDES["convars"], STRIDES["concommands"]


def addresses(blocks: list[int], sizes: list[int], stride: int) -> tuple[int, ...]:
    return tuple(b + 8 + i * stride for b, n in zip(blocks, sizes) for i in range(n))


def it_pins_the_strides():
    assert STRIDES == {"convars": 160, "concommands": 64}


class DescribeNameAt:
    @pytest.mark.parametrize("name", [b"x", b"sv_cheats", b"+attack", b"~" * 127])
    def it_reads_a_name(self, name: bytes):
        fake = Fake()
        addr = fake.string(name)
        mem, image = fake.load()
        assert name_at(mem, addr, image) == name.decode()

    @pytest.mark.parametrize(
        "name",
        [
            pytest.param(b"", id="empty"),
            pytest.param(b"sv cheats", id="space"),
            pytest.param(b"sv\tcheats", id="tab"),
            pytest.param(b"x" * 128, id="too-long"),
            pytest.param("café".encode(), id="non-ascii"),
        ],
    )
    def it_rejects_a_name_that_breaks_the_rule(self, name: bytes):
        fake = Fake()
        addr = fake.string(name)
        mem, image = fake.load()
        assert name_at(mem, addr, image) is None

    def it_rejects_a_name_outside_the_image(self):
        fake = Fake()
        fake.heap[HEAP] = bytearray(b"sv_x\0")
        mem, image = fake.load()
        assert name_at(mem, HEAP, image) is None


class DescribeWalk:
    def it_lists_entries_in_replay_order_across_blocks(self):
        fake = Fake()
        _, blocks = fake.queue(CONVAR, [fake.entry(b"v%d" % i) for i in range(250)])
        mem, image = fake.load()
        assert walk(mem, blocks[0], CONVAR, image, owned_ref) == addresses(blocks, [50, 100, 100], CONVAR)

    def it_accepts_a_full_root_block(self):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, [fake.entry() for _ in range(BLOCK)])
        mem, image = fake.load()
        assert walk(mem, blocks[0], COMMAND, image, owned_ref) == addresses(blocks, [100], COMMAND)

    def it_accepts_help_in_the_image(self):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, [fake.entry(help=b"some help, with spaces")])
        mem, image = fake.load()
        assert walk(mem, blocks[0], COMMAND, image, owned_ref) == addresses(blocks, [1], COMMAND)

    def it_returns_none_on_a_broken_link(self):
        fake = Fake()
        _, blocks = fake.queue(CONVAR, [fake.entry() for _ in range(150)])
        del fake.heap[blocks[1]]
        mem, image = fake.load()
        assert walk(mem, blocks[0], CONVAR, image, owned_ref) is None

    def it_returns_none_on_an_unreadable_link(self):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, [fake.entry()])
        fake.heap[blocks[0]] = fake.heap[blocks[0]][:-8]
        mem, image = fake.load()
        assert walk(mem, blocks[0], COMMAND, image, owned_ref) is None

    def it_returns_none_on_a_cycle(self):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, [fake.entry() for _ in range(200)])
        fake.poke(blocks[1] + 8 + BLOCK * COMMAND, "<Q", blocks[0])
        mem, image = fake.load()
        assert walk(mem, blocks[0], COMMAND, image, owned_ref) is None

    @pytest.mark.parametrize(
        ("block", "size"),
        [
            pytest.param(0, 0, id="empty-root"),
            pytest.param(0, BLOCK + 1, id="oversize-root"),
            pytest.param(1, BLOCK - 1, id="partial-older-block"),
        ],
    )
    def it_returns_none_on_a_bad_block_size(self, block: int, size: int):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, [fake.entry() for _ in range(150)])
        fake.poke(blocks[block], "<I", size)
        mem, image = fake.load()
        assert walk(mem, blocks[0], COMMAND, image, owned_ref) is None

    @pytest.mark.parametrize(
        ("field", "value"),
        [
            pytest.param(0, 0, id="null-name"),
            pytest.param(0, HEAP, id="name-outside-image"),
            pytest.param(8, HEAP, id="help-outside-image"),
        ],
    )
    def it_returns_none_on_an_entry_that_misfits(self, field: int, value: int):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, [fake.entry() for _ in range(150)])
        fake.poke(blocks[1] + 8 + 7 * COMMAND + field, "<Q", value)
        mem, image = fake.load()
        assert walk(mem, blocks[0], COMMAND, image, owned_ref) is None

    def it_returns_none_on_a_name_that_breaks_the_rule(self):
        fake = Fake()
        _, blocks = fake.queue(COMMAND, [fake.entry(), fake.entry(b"sv cheats")])
        mem, image = fake.load()
        assert walk(mem, blocks[0], COMMAND, image, owned_ref) is None

    def it_applies_the_ref_test_it_is_given(self):
        fake = Fake()
        odd = fake.qword(UNREGISTERED)
        _, blocks = fake.queue(COMMAND, [fake.entry(), fake.entry(ref=odd), fake.entry()])
        mem, image = fake.load()
        assert walk(mem, blocks[0], COMMAND, image, lambda mem, ref, image: True) == addresses(blocks, [3], COMMAND)
        assert walk(mem, blocks[0], COMMAND, image, lambda mem, ref, image: ref != odd) is None


PLACES = {"rdata": RDATA, "null": 0, "unmapped": HEAP + 0x7000000}
"""Refs the fake doesn't write: `.rdata`'s first qword reads 0; nothing is mapped at the last."""


class DescribeRefTests:
    def it_has_one_per_kind(self):
        assert REF_TESTS == {"convars": owned_ref, "concommands": unregistered_command_ref}

    @pytest.mark.parametrize(
        ("ref_test", "where", "value", "passes"),
        [
            (owned_ref, "data", 0, True),
            (owned_ref, "rdata", 0, False),
            (owned_ref, "heap", UNREGISTERED, False),
            (owned_ref, "null", 0, False),
            (unregistered_command_ref, "data", 0xFFFF, True),
            (unregistered_command_ref, "data", 0xDEAD_FFFF, True),
            (unregistered_command_ref, "heap", 0xFFFF, True),
            (unregistered_command_ref, "heap", 0, False),
            (unregistered_command_ref, "heap", 0xFFFE, False),
            (unregistered_command_ref, "heap", 0xFFFF_0000, False),
            (unregistered_command_ref, "null", 0, False),
            (unregistered_command_ref, "unmapped", 0, False),
        ],
    )
    def it_judges_a_ref_by_where_it_points_and_what_it_reads(self, ref_test: RefTest, where: str, value: int, passes: bool):
        fake = Fake()
        written = {"data": fake.qword, "heap": fake.heap_ref}
        ref = written[where](value) if where in written else PLACES[where]
        mem, image = fake.load()
        assert ref_test(mem, ref, image) is passes


class DescribeFindQueues:
    def it_finds_each_kind_in_a_two_queue_image(self):
        fake = Fake()
        convars = fake.queue(CONVAR, [fake.entry() for _ in range(3)])
        commands = fake.queue(COMMAND, [fake.entry() for _ in range(5)])
        mem, image = fake.load()
        assert find_queues(mem, image, "convars") == [Queue(convars[0], CONVAR, addresses(convars[1], [3], CONVAR))]
        assert find_queues(mem, image, "concommands") == [Queue(commands[0], COMMAND, addresses(commands[1], [5], COMMAND))]

    def it_finds_a_command_queue_with_a_heap_owned_command(self):
        fake = Fake()
        head, blocks = fake.queue(COMMAND, [fake.entry(), fake.entry(ref=fake.heap_ref()), fake.entry()])
        mem, image = fake.load()
        assert find_queues(mem, image, "concommands") == [Queue(head, COMMAND, addresses(blocks, [3], COMMAND))]

    def it_skips_a_command_queue_whose_ref_reads_anything_else(self):
        fake = Fake()
        _ = fake.queue(COMMAND, [fake.entry(), fake.entry(ref=fake.qword(0))])
        mem, image = fake.load()
        assert find_queues(mem, image, "concommands") == []

    def it_skips_a_convar_queue_with_a_ref_outside_the_writable_sections(self):
        fake = Fake()
        _ = fake.queue(CONVAR, [fake.entry(), fake.entry(ref=fake.heap_ref())])
        mem, image = fake.load()
        assert find_queues(mem, image, "convars") == []

    def it_skips_a_root_inside_the_image(self):
        fake = Fake()
        head, blocks = fake.queue(COMMAND, [fake.entry()])
        fake.rdata += bytes(-len(fake.rdata) % 8)
        root = RDATA + len(fake.rdata)
        fake.rdata += fake.heap.pop(blocks[0])
        struct.pack_into("<Q", fake.data, head - DATA, root)
        mem, image = fake.load()
        assert walk(mem, root, COMMAND, image, owned_ref) is not None
        assert find_queues(mem, image, "concommands") == []

    def it_reports_a_second_head_of_the_same_kind(self):
        fake = Fake()
        first = fake.queue(COMMAND, [fake.entry()])
        second = fake.queue(COMMAND, [fake.entry(), fake.entry()])
        mem, image = fake.load()
        assert [q.head for q in find_queues(mem, image, "concommands")] == [first[0], second[0]]

    def it_raises_on_an_unreadable_writable_section(self):
        fake = Fake()
        mem, image = fake.load()
        read = mem.read
        with pytest.raises(ShapeError):
            _ = find_queues(Memory(lambda addr, n: None if addr == DATA else read(addr, n)), image, "concommands")


class DescribeLearnStrides:
    def it_learns_a_stride_that_differs_from_the_pin(self):
        fake = Fake()
        head, blocks = fake.queue(168, [fake.entry() for _ in range(BLOCK + 1)])
        mem, image = fake.load()
        assert learn_strides(mem, image) == [Queue(head, 168, addresses(blocks, [1, 100], 168))]
        assert 168 not in STRIDES.values()

    def it_owner_checks_whatever_the_stride(self):
        fake = Fake()
        entries = [fake.entry() for _ in range(BLOCK + 1)]
        entries[3] = fake.entry(ref=fake.heap_ref())
        _ = fake.queue(COMMAND, entries)
        mem, image = fake.load()
        assert learn_strides(mem, image) == []

    def it_ignores_a_single_block_queue(self):
        fake = Fake()
        _ = fake.queue(CONVAR, [fake.entry() for _ in range(BLOCK)])
        mem, image = fake.load()
        assert learn_strides(mem, image) == []

    def it_raises_on_a_head_that_two_strides_fit(self):
        """Every qword of the blocks points at a name in `.data`, so any offset
        passes as name, help or ref; only the `m_pPrev` slots tell strides apart.
        Stride 40's `m_pPrev` lands at +16 of a stride-48 entry, which is unchecked."""
        fake = Fake()
        name = fake.qword(int.from_bytes(b"x\0", "little"))
        blocks = [HEAP, HEAP + 0x100000]
        for block, prev in zip(blocks, [blocks[1], 0]):
            raw = bytearray(struct.pack("<Q", BLOCK) + struct.pack("<Q", name) * (BLOCK * 48 // 8) + bytes(8))
            for stride in (40, 48):
                struct.pack_into("<Q", raw, 8 + BLOCK * stride, prev)
            fake.heap[block] = raw
        _ = fake.qword(blocks[0])
        mem, image = fake.load()
        with pytest.raises(ShapeError):
            _ = learn_strides(mem, image)
