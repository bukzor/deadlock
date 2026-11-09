---
managed-by: Skill(llm-subtask)
status: done
blocked-by:
  - 2026-11-09-004-dllscan-reglist.md
  - 2026-11-09-005-dllscan-win32-and-winpy.md
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-004-dllscan-reglist.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/2026-11-09-005-dllscan-win32-and-winpy.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
  - docs/dev/convar-dump.kb/CLAUDE.md
  - docs/dev/convar-dump.kb/capture-approach.kb/queue-shape-scan.md
  - docs/dev/convar-dump.kb/registration-flow.md
---

# `rendersystemdx11` owner-check exception: gather the evidence

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (the step "Settle the
`rendersystemdx11` owner-check exception")

## Problem Statement

On build 6851, 6 of 7 entries in `rendersystemdx11.dll`'s queue passed the
probe's owner check (`queue-shape-scan.md`, `[!QUESTION]`). `reglist` is
strict, so on that DLL it probably finds no queue, or a truncated one. This
unit **gathers evidence and recommends**; it does not decide. The KB rule is
"never implement a `[!QUESTION]`", and the user or coordinator closes it from
your report.

On the real install (6860), with a throwaway driver in `trash/` run through
`bin/winpy`, using `win32` + `image` + `reglist`:

1. What strict `reglist.find_queues` returns on `rendersystemdx11.dll` for
   both strides. The DLL must load cleanly: check that it isn't one of the
   four hang-listed DLLs and that its imports aren't either.
2. Find the odd entry. Use `learn_strides`, or walk with the check loosened
   in your driver only. Dump its raw bytes and decode every pointer field:
   where each points (which module, which section, or null), and what the
   trailing ref is.
3. Compare it with the passing entries of the same queue, and with a
   `server.dll` entry. Using `registration-flow.md` and the s2sdk struct
   (`docs/dev/convar-dump.kb/CLAUDE.md` pins the commit; clone it into
   `trash/` if needed), say what that field is and why it differs: a null
   default callback, a ref into another module, or something else.
4. Run the same scan over every DLL that loads, apart from the hang list.
   Which other DLLs, if any, show the same exception? This tells whether a
   tolerance rule is a one-off or general.

**Report:** the facts above with the build number. Then a recommendation:
a strict check plus a named exception, or the tolerance `reglist`'s Open
Question proposes, or another option. Give the false-positive risk of each,
in numbers where you have them. Propose the exact sentence that would replace
the `[!QUESTION]` callout, but do not edit `docs/`.

**Scope:** `trash/` only. No edits to `src/`, `docs/` or `bin/`.

## Steps

- [x] Hang check: static + delay-import closure of all 97 DLLs (`trash/rdx/closure.py`, pefile): only the 4 hang-listed DLLs reach a hang-listed DLL; `rendersystemdx11` is clean
- [x] Drivers `trash/winpy/rdx_scan.py` (strict `find_queues` + the same walk minus the ref test, every ref classified by module/section or `VirtualQuery`), `rdx_time.py`; `trash/rdx/scan_all.sh` over the 93 non-excluded DLLs; results `trash/rdx/*.json{,l}`, `summarize.py`
- [x] Odd entry decoded; compared with its queue, `server.dll`, s2sdk `18139bd` (`trash/s2sdk-18139bd`)

## Decisions

- `learn_strides` can't see a 7-entry queue (needs >1 block): loosened the ref test in the driver instead.
- Command entry decoded per s2sdk `ConCommandCreation_t` (`convar.h:382-493`): +24 callback, +32 bitfield byte (bit0 `m_bIsInterface`), +40 completion, +48 its flag, +56 `m_Command`.

## Open Questions

- [ ] For the plan (not this unit): `nvngx_dlss.dll` (43 MB `.data`) takes 15 s per strict `find_queues` pass, ~55 s for this driver's 4 passes: `winpy`'s 60 s default is marginal for a `reglists`-merged atom. `phonon4.dll` and `vfx_dx11.dll` fail `LoadLibraryExW` 126 on 6860 (the KB lists only `vfx_dx11`).

## Final report

Build 6860. Scope kept: `trash/` only; no `src/`, `docs/`, `bin/`, git index.

**1. Strict `find_queues` on `rendersystemdx11`:** convars one queue, 51 entries (`.data+0x496280`); concommands **none**. The DLL loads cleanly.

**2. The odd entry:** index 4 of 7, `r_textures_evict_all`. Name/help in `.rdata`; flags `0x100000003`; +24 callback = a heap address (`MEM_PRIVATE`, committed, `PAGE_READWRITE`); +32 bit0 = 1 (callback is an `ICommandCallback*`); +56 ref = callback + 0x10, same heap block. At callback: two vtable pointers into `rendersystemdx11` `.rdata`, then (ref+0) u16 `0xFFFF`, ref+8 `m_pOwner` = callback - 0x18 (an object whose own vtables are in `.rdata`), ref+0x10 `m_Func` in `.text`.

**3. What it is:** a `CConCommandMemberAccessor<T>` (`convar.h:1514`: `ICommandCallback`, `ICommandCompletionCallback`, then `ConCommand` at +0x10; it passes `this` as the callback) that is a member of a heap-allocated `T`, built before `ConVar_Register`, so `SetupConCommand` queued `m_Command` = a heap `ConCommand`. Not null, not another module. It is legal: replay only writes `*m_Command` (`convar.cpp:52`). The passing entries `r_gpu_mem_stats`, `r_print_buffers`, `r_dx11_report_live_objects` are the same class as statics (callback in `.data`, ref = callback + 0x10). `server.dll` (2008 convars / 493 commands): 482 commands have a `.text` function callback, 11 a static interface in `.data`; every ref is in `.data`. Convar refs are `&ConVar::m_ConVarData` (entry +152 = +144 + 8, all 6223).

**4. All DLLs:** 91 of 93 non-excluded load, 35 carry queues: 6223 convars, 1418 commands (1411 strict + rdx's 7; `client` 2289/428, `engine2` 423/220, `tier0` 3/24). Of 7641 real entries, **1** ref is outside the DLL's writable sections: this one. Every command ref (1418/1418) reads u16 `0xFFFF` (`kInvalidAccessIndex`, `ConCommandRef()` at `convar.h:536-540`). With the ref test dropped, stride 64 finds nothing new; stride 160 adds exactly 4 one-entry queues (`inputsystem`, `panoramauiclient`, `vphysics2`, `vscript`: their command queue read at the convar stride), each with a **null** ref.

**Options, false positives on 6860:**
- Strict (as built): 0 FP, 1 queue silently lost (a DLL with no queue is accepted).
- Strict + named exception (`rendersystemdx11`/`r_textures_evict_all`): 0 FP; the next heap-owned command anywhere is lost silently again; a name list to maintain.
- `reglist` OQ "null refs": doesn't fix rdx (its ref is not null), admits all 4 spurious (4 FP). "k misses", k≥1: fixes rdx, admits all 4 (each misses 1 of 1).
- **Recommended:** per-kind ref test. Commands: ref readable and u16 at ref == `0xFFFF` (an unregistered `ConCommandRef`; location-free, so heap-owned commands pass); 1418/1418 pass, 0 FP (the owner test rejected nothing else at stride 64). Convars: keep the owner check (6223/6223; it rejects the 4). Pure over `Memory`; `walk` and `learn_strides` stay single-rule. Risk: a garbage candidate whose ref happens to hit `0xFFFF`, which still needs every entry's name and help to fit first.

**Proposed replacement for the `[!QUESTION]`** (and pass 2's "last qword … own writable sections" sentence then says "convar entries"):

> A command entry's ref is the `ConCommand` that queued it, which need not be a global: `rendersystemdx11`'s `r_textures_evict_all` is a `CConCommandMemberAccessor` inside a heap object (6851, 6860). So a command ref must read as an unregistered `ConCommandRef` (u16 `0xFFFF`, s2sdk `convar.h:536`), which holds for all 1418 command entries on 6860. Convar refs keep the owner check (6223 of 6223 entries); that is what rejects the four one-entry command queues read at the convar stride.
