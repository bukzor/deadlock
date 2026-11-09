---
managed-by: Skill(llm-subtask)
status: done
---

# `dllscan.flags`: FCVAR bit → name

**Priority:** part of the parent's `src/dllscan/` build-out
**Complexity:** low
**Context:** parent plan <https:../2026-11-05-000-per-dll-dump-tree.md> (`src/dllscan/` section);
`docs/dev/convar-dump.kb/` (`CLAUDE.md` prior-art pins, `registration-flow.md`,
`output-views.md`, `validation.md`); `docs/dev/probes/convar_scan.py` (no flag table)

## Problem Statement

Write `src/dllscan/flags.py` + `flags_test.py` only: a public function from the
int flag word to its names, plus the table itself. Bits from s2sdk `deadlock` at
`18139bd`; names lowercased, `FCVAR_` dropped, spelled as DumpSource2 (`00759ce`)
spells them (DumpSource2 wins on disagreement, so output diffs against
GameTracking-Deadlock's `DumpSource2/convars.txt`). Unknown bit → `flag_<n>`.
Module docstring cites the source commits. Stdlib only, 3.12-compatible, ≤300
lines; Describe/it tests incl. an unknown bit and a multi-bit word, each
assertion observed failing. Sources cloned fresh into gitignored `trash/`. No
git staging/commits; don't touch `pyproject.toml`, `memory.py`, `document.py`,
the parent plan, or docs. Done = pytest and pyright clean on both files.

## Implementation Steps

- [x] Fetch s2sdk `18139bdc96f1` into `trash/s2sdk-18139bd/` (existing `trash/s2sdk/` is loose files, unpinned)
- [x] Confirm `trash/DumpSource2/` is at `00759ce86fa6`
- [x] Diff s2sdk defines against DumpSource2's `g_flagMap`
- [x] Tests first, observe red (8/9 red on a stub; `names(0)` and the short-circuited
  `BY_BIT[37]` driven red by mutation, as were order, bit-vs-mask, and the doctest)
- [x] Implement; green
- [x] pyright clean

## Decisions

- **Bits live in `public/tier0/convar.h:174-231`**, not `tier1/` as briefed.
- **Names: DumpSource2's `g_flagMap`** (`src/main/dumpers/concommands/concommands.cpp:51-88`).
  It names every s2sdk define. Sole spelling discrepancy vs naive
  lowercase-unprefix: `FCVAR_NOT_CONNECTED` → `notconnected` (DumpSource2 wins).
  s2sdk's own `ConVar_PrintDescription` map (`game`, `client`, `singleplayer`, …)
  is a console-display subset, ignored.
- **Unknown bits → `flag_<bit index>`**, matching DumpSource2's `GetFlagNames`.
- **Order: named flags in bit order, then unnamed `flag_<n>` in bit order** —
  DumpSource2's `GetFlagNames` order, which is what `convars.txt` prints. Deviates
  from the brief's "ascending bit order" only when an unnamed bit sits below a
  named one (31 or 35 together with a higher named bit).
- **Return `tuple[str, ...]`**: immutable; table is `Mapping[int, str]` keyed by bit index.

## Open Questions

None blocking. For `entries`/aggregators, not this module: DumpSource2's
`schemas.json` (not `convars.txt`) sorts flag names alphabetically, drops
`gamedll`/`clientdll` for server/client, and appends a pseudo-flag
`workshop_whitelisted`; none of that belongs in a bit table.

## Final report

Files: `src/dllscan/flags.py` (67 lines), `src/dllscan/flags_test.py` (45 lines).
API: `BY_BIT: Mapping[int, str]` (bit index → name, 36 entries: bits 0–30,
32–34, 36–37) and `names(flags: int) -> tuple[str, ...]` (asserts
`0 <= flags < 2**64`). Sources: s2sdk 18139bdc96f1 (`public/tier0/convar.h`),
DumpSource2 00759ce86fa6 (`concommands.cpp`), the s2sdk commit DumpSource2 vendors.
Checks: `pytest src/dllscan` 36 passed (flags: 9 tests + doctest);
`pyright` on both files 0 errors.
