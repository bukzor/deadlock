# How to capture the registrations: read each DLL's queues, located by their allocation

The question: at which point in `registration-flow.md` do we read the cvars, so
that the result is complete (dev-only included), deterministic, and the
version-specific knowledge we depend on is as small, and as self-checking, as
possible?

The answer: load each DLL in a process of its own and read its reg-list
queues, with no code signatures and no engine startup. Each queue is located
by watching tier0's allocator hand out its blocks
(`capture-approach.kb/allocator-hook.md`), for every DLL but tier0, whose
queues are built before any hook can be placed; tier0's are found by their
data shape (`capture-approach.kb/queue-shape-scan.md`). Both read entries at
the two strides of s2sdk's layout (`dllscan.reglist.STRIDES`). It covers
every DLL whose load is `ok` (`dll-coverage.md`), each on its own
(`output-views.md`). On 6860 that is 30 convar and 30 command queues (6223
and 1418 declarations).

Why it meets each criterion:

- **Complete.** The queue is lossless: every one of `server.dll`'s 2008
  `RegisterConVar` calls on 6854 is a queue entry, duplicates included, and
  `developmentonly` entries are queued like any other.
- **Deterministic.** It needs only `LoadLibrary`, with no `Connect` or `Init`,
  and its documents hold no addresses. A queue's head is an equality on a
  pointer the allocator returned, not a search, and a DLL with no queue is
  one that allocated no block.
- **Small, self-checking knowledge.** It relies on the reg-list shape, the
  entry layout from s2sdk's `convar.h` (`src/dllscan/convar_h.py`), and
  tier0's `MemAlloc_AllocFunc`, from which the allocator's slot is read on
  every load. Each part fails loudly when it stops fitting (`validation.md`,
  "Shape").

Two things kept the question open, and both are settled. The value fields
decode by the binary's own type table, and the layout fits tier0's registry
for every convar `server` and `client` declare once (6860,
`registration-flow.md`, "The convar entry's layout"). The one owner-check
exception, `rendersystemdx11`'s heap-owned command, became a per-kind ref test:
a command's ref must read as an unregistered `ConCommandRef`, and a convar's
ref keeps the owner check (`capture-approach.kb/queue-shape-scan.md`).

The hook (`capture-approach.kb/icvar-hook.md`) works (`Init` runs the replay)
but adds no declarations. It is the instrument for the engine's side: the value
layout was fit against its registry readback, the readback check
(`validation.md`) runs it on demand, and the engine's merged view
(`output-views.md`) is its later use.

The candidates, chosen and declined alike, are in `capture-approach.kb/`.
