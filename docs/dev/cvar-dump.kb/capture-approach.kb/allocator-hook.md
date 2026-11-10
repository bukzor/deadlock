# Find each DLL's queue by its blocks' allocation (weighed, not built)

The question this answers is the one inside `./queue-shape-scan.md`: where is
the unexported `s_pRoot`? The queue-shape scan searches every writable qword
for something shaped like a queue. This instead watches the queue being
built. `AddToList`'s `new ConVarRegList` (`../registration-flow.md` step 2) is
a call across the DLL boundary into tier0's allocator, made during
`LoadLibrary`, so interposing that allocator hands us each block's address
as a return value.

Mechanism, build 6860:

- **One slot sees every allocation.** tier0 exports `g_pMemAlloc` (`.data`
  RVA 0x3ac618) and `MemAlloc_AllocFunc`; game DLLs import one or both.
  `MemAlloc_AllocFunc` is `mov rdx, rcx; mov rcx, [g_pMemAlloc]; mov rax,
  [rcx]; jmp [rax+8]` (`../../probes/disas.py`), so both routes reach
  vtable slot 1, `Alloc(this, size)`. They arrive by jump, not call, so the
  return address the slot sees is the game DLL's own call site.
- **The hook.** Load tier0 and point its `g_pMemAlloc` object at a private
  vtable: a call-through stub on slot 1 that logs size, caller and returned
  pointer, and tail-jump loggers on the other 43 slots. Then load the DLL
  under test. The stubs are hand-encoded x64 (`../../probes/alloc_trace.py`,
  checked with capstone).
- **Locate from the log.** A block is `16 + 100·sizeof(Entry_t)` bytes:
  16016 for convars, 6416 for commands. The head is the DLL's writable qword
  that holds the newest logged block of that size, and the chain from it
  must close over exactly the logged blocks of that size.

Evidence, 6860, all 91 DLLs whose load is `ok` (`../../probes/winpy_all.sh`
over `alloc_trace.py`; summaries in `../../probes/alloc_trace_6860.jsonl`):

- **Every block is a logged allocation.** In the 34 DLLs other than tier0
  that have queues, every block the shape scan finds is a slot-1 allocation,
  made from inside that DLL, of exactly its kind's size. No allocation of
  either size is anything but a block.
- **The log alone locates every queue.** Each kind has exactly one head slot
  holding the newest block, its chain closes over exactly the logged blocks,
  and the result agrees with the scan. Per DLL and kind, the entry counts
  equal the committed store's.
- **Absence is proven.** The other 56 DLLs make no allocation of either size,
  including the 8 that load tier0 and yield no queue (`../dll-coverage.md`).
- **The log is repeatable.** A rerun on `server` and `engine2` gives
  byte-identical summaries (84,457 allocator calls on `server`).
- **Exact sizes matter.** The looser rule "any `16 + 100k`" admits one stray
  816-byte allocation in `client`; `convar_h`'s sizes don't.

The gap is tier0 itself. tier0 allocates its own queues (3 convars, 24
commands) in its own static initializers, before `LoadLibrary` returns. Even
from a loader notification, which runs once tier0 is mapped and before its
initializers, `g_pMemAlloc` is still null (`../../probes/tier0_alloc.py`, two
runs), so no hook can be in place in time.

For, over the shape scan's search: the head is an equality on a pointer the
allocator returned, not a search, so nothing depends on which heap garbage
ASLR puts in the writable sections. A decode misfit then fails loudly
instead of hiding its queue, and "no queue" is an observed fact rather than
a failure to find one. The stride is confirmed by the binary's own
allocation size on every load. It still needs only `LoadLibrary`: no
`Connect` or `Init`.

Against: native stubs in the scanner (the registry readback already carries
one, `dllscan.registry`). It relies on the allocator's slot order (slot 1
is Alloc), which is read from `MemAlloc_AllocFunc`'s code. tier0 still needs
the shape scan.

> [!QUESTION] Whether this replaces the shape scan's search for every DLL
> but tier0, keeping the scan for tier0 alone.
