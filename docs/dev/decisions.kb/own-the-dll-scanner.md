---
status: accepted
date: "2026-11-09"
---

# Own the DLL scanner, not an upstream dumper

The project writes and maintains its own cvar scanner, `src/dllscan/`. It loads
each game DLL in Windows Python and reads the DLL's reg-list queues from memory
(`../cvar-dump.kb/capture-approach.md`). On its face that breaks
`reuse-existing-parsers.md`. It is that decision's own exception instead: no
tool we would trust covers the need. Leave it in place. Don't swap it for an
upstream dump.

## Why

- **The source must be ours.** The user does not trust a special-purpose
  third-party dumper (DumpSource2, or GameTracking-Deadlock's output of it) to
  be the source (2026-11-05). It is still a second opinion: on 6854, 1991 of
  2002 registry defaults equal its dump.
- **Upstream is lossy where we need lossless.** DumpSource2 merges same-named
  declarations into one (`MergeQueued`). The store keeps every declaration,
  per DLL, duplicates included (`../cvar-dump.kb/output-views.md`).
- **No parser exists for this.** A reg-list queue is in-memory state built by
  static initializers, not a file format. `pefile` and VRF read files, and the
  values are built by code, so no static table holds them.
- **The knowledge is small and fails loudly.** The scanner depends on the
  reg-list shape and s2sdk's entry layout, transcribed once as `ctypes`
  structs (`dllscan.convar_h`). Pinned strides, anchors, and a typed decode
  break the build when a patch moves them (`../cvar-dump.kb/validation.md`).

The scanner is stdlib-only: it runs in a bare `python.exe` with `src/` on its
path (`bin/winpy`), so the Windows side has no environment to provision. That
also rules out reusing PyPI packages there. WSL-side code keeps reusing as
before (a later `pe` facet is to use `pefile`).

## Alternatives weighed

All of them are in `../cvar-dump.kb/capture-approach.kb/`: DumpSource2's
output, its code-signature scan, `cvarlist` in the running game, a registry
walk after `Connect`, an `ICvar` hook, and static analysis. Each one lost on
trust, loss, coverage of `developmentonly`, or brittleness.

## What would change this

A maintained tool that the user trusts and that dumps every declaration per DLL,
offline and losslessly (duplicates, `developmentonly`, typed values). Or a
patch cadence that breaks the shape scan more often than an upstream tool's
signatures break.
