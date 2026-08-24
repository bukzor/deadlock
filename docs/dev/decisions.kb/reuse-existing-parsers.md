---
status: accepted
date: "2026-06-15"
---

# Reuse existing parsers instead of hand-rolling

Parsing Source 2 is a well-trodden path; depend on mature tools rather than
writing our own format parsers.

- **`vpk`** (PyPI, ValvePython) — VPK v2 container layer: list entries, read raw
  bytes, CRC32 per file. Validated against the real `pak01_dir.vpk`
  (129,814 entries). Stale (2021) but the v2 container format is stable.
- **`keyvalues3`** (PyPI) — KV3 text and binary (incl. compiled block versions).
  Kept as the reference implementation (test oracle), but off the hot path: its
  parsimonious-based text reader took ~26s on `scripts/abilities.vdata` alone
  (~37s of a 38s full build). `deadlock.kv3text` is a small recursive-descent
  reader for the machine-generated KV3 subset VRF emits, verified by
  output-equality against `keyvalues3` across the corpus.
- **ValveResourceFormat / `Source2Viewer-CLI`** — the canonical decompiler. The
  only tool that turns compiled `_c` resources into usable assets
  (`vtex_c`→png, `vmdl_c`→glTF, `vsnd_c`→wav) and decompiles `vdata_c`→KV3.

## Alternatives weighed

- Hand-rolling a Source 2 resource-block parser: large, and a moving target VRF
  already tracks (Deadlock-specific blocks land in VRF first).
- `srctools`: strong for Source 1, not a Source 2 `_c` decompiler.

## What would change this

Drop a dependency only if it blocks a needed feature (e.g. `vpk`'s lack of
multi-archive *write* support — irrelevant, we only read). A small bespoke
parser is justified only where no tool covers the need (e.g. block-level diffing
finer than VRF exposes), built on `deadlock.binary` — or where the existing
parser's cost dominates the build and an oracle test pins equivalence
(`deadlock.kv3text`, 2026-08).
