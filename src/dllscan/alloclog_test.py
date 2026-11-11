import struct
from collections.abc import Iterable
from typing import cast

import capstone
import pytest

from .alloclog import RECORD, RECORDS, SIZES, Alloc, alloc_slot, locate, read_log, stub
from .memory import Memory, Segments
from .reglist import STRIDES
from .reglist_fake import HEAP, Fake, logged
from .shape import ShapeError


def it_sizes_a_block_as_its_header_entries_and_link():
    assert SIZES == {"convars": 16016, "concommands": 6416}


ALLOC_FUNC = bytes.fromhex("488bd1488b0dbee82700488b0148ff6008")
"""tier0's `MemAlloc_AllocFunc` at RVA 0x12dd50 on 6860, `g_pMemAlloc` at 0x3ac618."""
LOG, ORIG = 0x1111111111111111, 0x2222222222222222


def disassemble(code: bytes) -> list[str]:
    """`code` at address 0, one line per instruction; it must decode whole."""
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    lite = md.disasm_lite(code, 0)  # pyright: ignore[reportUnknownMemberType]
    insns = list(cast(Iterable[tuple[int, int, str, str]], lite))
    assert sum(size for _, size, _, _ in insns) == len(code), insns
    return [f"{at:#x} {mnemonic} {ops}".rstrip() for at, _, mnemonic, ops in insns]


class DescribeAllocSlot:

    def it_reads_the_slot_from_the_jump(self):
        assert alloc_slot(ALLOC_FUNC[:-1] + b"\x18", 0x12DD50, 0x3AC618) == 3

    def it_refuses_another_global(self):
        with pytest.raises(ShapeError, match="MemAlloc_AllocFunc"):
            _ = alloc_slot(ALLOC_FUNC, 0x12DD50, 0x3AC620)

    @pytest.mark.parametrize("at", [0, 7, 12, 16])
    def it_refuses_other_code(self, at: int):
        code = bytearray(ALLOC_FUNC)
        code[at] ^= 0x01
        with pytest.raises(ShapeError, match="MemAlloc_AllocFunc"):
            _ = alloc_slot(bytes(code), 0x12DD50, 0x3AC618)


class DescribeStub:
    def it_tail_calls_any_other_size_and_logs_each_given_one(self):
        assert disassemble(stub(LOG, ORIG, [16016, 6416])) == [
            "0x0 cmp rdx, 0x3e90",
            "0x7 je 0x1f",
            "0x9 cmp rdx, 0x1910",
            "0x10 je 0x1f",
            "0x12 movabs r10, 0x2222222222222222",
            "0x1c jmp r10",
            "0x1f sub rsp, 0x38",
            "0x23 mov qword ptr [rsp + 0x20], rdx",
            "0x28 mov rax, qword ptr [rsp + 0x38]",
            "0x2d mov qword ptr [rsp + 0x28], rax",
            "0x32 movabs rax, 0x2222222222222222",
            "0x3c call rax",
            "0x3e movabs r10, 0x1111111111111111",
            "0x48 mov r11d, 1",
            "0x4e lock xadd qword ptr [r10], r11",
            f"0x53 cmp r11, {RECORDS:#x}",
            "0x5a jae 0x79",
            "0x5c shl r11, 5",
            "0x60 add r11, r10",
            "0x63 mov rdx, qword ptr [rsp + 0x20]",
            "0x68 mov qword ptr [r11 + 8], rdx",
            "0x6c mov rdx, qword ptr [rsp + 0x28]",
            "0x71 mov qword ptr [r11 + 0x10], rdx",
            "0x75 mov qword ptr [r11 + 0x18], rax",
            "0x79 add rsp, 0x38",
            "0x7d ret",
        ]


class DescribeReadLog:
    def it_reads_the_records_in_claim_order(self):
        raw = struct.pack("<4Q", 3, 0, 0, 0) + struct.pack("<4Q", 0, 16016, 0x10, 0x20) + struct.pack("<4Q", 0, 6416, 0x30, 0x40)
        assert read_log(Memory(Segments({0x1000: raw})), 0x1000) == [Alloc(16016, 0x10, 0x20), Alloc(6416, 0x30, 0x40)]

    def it_reads_an_empty_log(self):
        assert read_log(Memory(Segments({0x1000: struct.pack("<Q", 1)})), 0x1000) == []

    def it_refuses_a_full_log(self):
        raw = struct.pack("<Q", RECORDS + 1).ljust(RECORD * RECORDS, b"\0")
        with pytest.raises(ShapeError, match="allocation log full"):
            _ = read_log(Memory(Segments({0x1000: raw})), 0x1000)


class DescribeLocate:
    def it_finds_a_queue_by_its_newest_block(self):
        fake = Fake()
        head, blocks = fake.queue(STRIDES["convars"], [fake.entry(b"v%d" % i) for i in range(250)])
        mem, image = fake.load()
        queue = locate(mem, image, "convars", logged("convars", blocks))
        assert queue is not None
        assert (queue.head, queue.stride, len(queue.entries)) == (head, 160, 250)

    def it_is_none_when_the_dll_allocated_no_block_of_that_kind(self):
        fake = Fake()
        _, blocks = fake.queue(STRIDES["convars"], [fake.entry()])
        mem, image = fake.load()
        assert locate(mem, image, "concommands", logged("convars", blocks)) is None

    def it_ignores_blocks_another_module_allocated(self):
        fake = Fake()
        _, blocks = fake.queue(STRIDES["concommands"], [fake.entry()])
        mem, image = fake.load()
        assert locate(mem, image, "concommands", logged("concommands", blocks, caller=HEAP)) is None

    def it_refuses_a_newest_block_no_slot_holds(self):
        fake = Fake()
        _, blocks = fake.queue(STRIDES["concommands"], [fake.entry()])
        fake.data[-8:] = bytes(8)  # the head slot
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="concommands head slots"):
            _ = locate(mem, image, "concommands", logged("concommands", blocks))

    def it_refuses_a_newest_block_two_slots_hold(self):
        fake = Fake()
        _, blocks = fake.queue(STRIDES["concommands"], [fake.entry()])
        _ = fake.qword(blocks[0])
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="concommands head slots"):
            _ = locate(mem, image, "concommands", logged("concommands", blocks))

    def it_refuses_a_queue_that_misfits(self):
        fake = Fake()
        _, blocks = fake.queue(STRIDES["concommands"], [fake.entry(ref=fake.qword(0))])
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="concommands queue misfits"):
            _ = locate(mem, image, "concommands", logged("concommands", blocks))

    def it_refuses_a_logged_block_the_chain_skips(self):
        fake = Fake()
        _, stray = fake.queue(STRIDES["convars"], [fake.entry()])
        _, blocks = fake.queue(STRIDES["convars"], [fake.entry()])
        mem, image = fake.load()
        with pytest.raises(ShapeError, match="convars chain and allocations differ"):
            _ = locate(mem, image, "convars", logged("convars", stray + blocks))

    def it_refuses_blocks_logged_out_of_chain_order(self):
        fake = Fake()
        _, blocks = fake.queue(STRIDES["convars"], [fake.entry() for _ in range(250)])
        mem, image = fake.load()
        log = logged("convars", blocks)
        log[0], log[1] = log[1], log[0]
        with pytest.raises(ShapeError, match="convars chain and allocations differ"):
            _ = locate(mem, image, "convars", log)
