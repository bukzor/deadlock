# Find each DLL's queue by its data shape (chosen)

After `LoadLibrary` (no `Connect`), scan the DLL's writable sections for a
pointer to a heap block shaped like a reg-list (`../registration-flow.md` step
2): `u32 m_nSize` (≤100), then entries at a fixed stride whose first two fields
are a name pointer into the DLL's image (printable, NUL-terminated) and a help
pointer (null or into the image), then `m_pPrev` at `8 + 100·stride`, chaining
back through full 100-entry blocks. Reads go through `ReadProcessMemory` on our
own process, so a wrong guess is a failed read, not a crash.

Two passes:

1. **Learn the strides from `server.dll`.** Try 16..1016 and keep heads where
   exactly one stride fits every entry over more than one block. Exactly two
   heads survive; anchors (`../validation.md`) decide which stride is convars. A
   single block can't fix a stride — schema/datamap objects also lead with name
   pointers and admitted dozens of false positives — so this pass needs a DLL
   with multi-block queues.
2. **Scan every DLL that loads (`../dll-coverage.md`) at those two strides**, any
   length, keeping a head only if every entry's last qword (the ref the static
   initializer queued) passes its kind's ref test. For convar entries it must
   point into that DLL's own writable sections (the owner check); command
   entries have their own test, below.

The scanner pins the strides (160/64, `dllscan.reglist.STRIDES`), so each
DLL's dump depends on nothing but that DLL (`../output-views.md`). Pass 1 is a
check target of its own, `data/dlls.check/strides`: it re-learns the strides
from `server.dll` every build and fails the build if they moved
(`../validation.md`).

Evidence, pass 1, build 6848 (`../../probes/convar_scan.py`, 2026-11-05):

| DLL | convar queue (stride 160) | command queue (stride 64) |
|---|---|---|
| `server.dll` | 2007 | 493 |
| `client.dll` | 2288 | 427 |
| `engine2.dll` | 423 | 220 |

Each convar head is the address DumpSource2's code signature resolves to, found
independently. Flags read at entry `+16` decode to upstream's for every anchor
checked (`citadel_bot_kick` `0x100000002` = developmentonly|defensive;
`bot_kick_all` `0x2004000` = cheat|client_can_execute;
`citadel_lane_swap_available_duration_prematch` `0x6000` = replicated|cheat),
and help strings match.

Evidence, pass 2, build 6851 (`../../probes/fixed_stride_scan.py`, results in
`../../probes/fixed_stride_6851.jsonl`, 2026-11-05), strides fixed at 160/64 over
the 42 DLLs that load: 35 yield queues, 6 yield none. 6221 convar and 1417
command declarations — 1503 and 277 more than the three DLLs above. `server` and
`client` counts are unchanged from 6848. `tier0` has its own queues (24
commands incl. `find`, 3 convars). The owner check is what makes short queues
discriminating: without it, `inputsystem`, `panoramauiclient`, `vphysics2` and
`vscript` each show a spurious one-entry convar queue (owner check 0/1), their
one-entry command queue read at the convar stride, where nothing past entry 0
gets checked. With it, every DLL has at most one queue of each kind.

A command entry's ref is the `ConCommand` that queued it, which need not be a
global: `rendersystemdx11`'s `r_textures_evict_all` is a
`CConCommandMemberAccessor` inside a heap object (6851, 6860). So a command ref
must read as an unregistered `ConCommandRef` (u16 `0xFFFF`, s2sdk
`convar.h:536`), wherever it points, which holds for all 1418 command entries on
6860. Convar refs keep the owner check (6223 of 6223 entries); that is what
rejects the four one-entry command queues read at the convar stride. Pass 1 runs
before any kind is known, so it owner-checks every entry at every stride: the
one heap-owned ref on 6860 sits in a single-block queue, which pass 1 skips
anyway.

For: no code signatures, no vtable slots, no `Connect`; the version-specific
knowledge is the reg-list shape (`m_nSize`, 100, `m_pPrev`) and the name/help/flags
prefix of the creation struct, and the scan fails rather than misreads if those
change. Strides come out of the data; which stride is convars is decided by
anchors, not by assumption.

Against: the value fields past `+16` (type, default, min, max) follow the SDK
layout, checked against tier0's registry rather than derived from the data
(`../registration-flow.md`, "The convar entry's layout"). Pass 2 assumes every DLL was built against the same SDK as
`server.dll`; a DLL whose queue used another stride would scan as having none,
which only the oracle (`runtime-cvarlist.md`) would notice.
