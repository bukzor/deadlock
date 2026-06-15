--- # workaround: anthropics/claude-code#13003
git-caution: personal
requires:
    - Skill(llm-kb)
---

# deadlock

Deterministic, repeatable parsing/inspection of the Deadlock (Source 2) game
binary, to: diff patch changes precisely, understand game mechanics from data
(not black-box play), and view assets (models, textures, audio).

## Working in this repo

- Run anything through the environment with `./bin/shell <cmd>` (loads direnv:
  `.venv` + `bin/` on PATH). E.g. `./bin/shell pytest`, `./bin/shell pyright`.
- Python via `uv` (managed CPython, pinned in `.python-version`). Add deps with
  `uv add`; never hand-edit the lock.
- **Reuse before inventing.** Lean on existing tools (`vpk`, `keyvalues3`,
  ValveResourceFormat) rather than hand-rolling parsers. See
  `docs/dev/decisions.kb/`.
- Python modules ≤300 lines; bash ≤50 lines (only for fs/process work or
  `python -m` shims). Style/TDD conventions are the house defaults
  (`~/.claude/reference.kb/python/`).
- Tests live beside their module as `{module}_test.py`, Describe/it naming;
  doctests run automatically. Observe every assertion fail before trusting it.
- Generated output goes under `data/` (gitignored) and is regenerated with
  `redo`. Never commit extracted assets or vendored tools.

## Knowledge bases (`docs/dev/`)

Three `llm-kb` knowledge bases, each a directory of per-topic files — `ls` them
to see the full range; read the one whose name matches before acting.

- `decisions.kb/` — why the project is built the way it is, one file per choice:
  reuse existing parsers, generated output under `data/` via `redo`, commit
  line-grained diffable data (no bespoke diff), tests alongside modules, VRF runs
  natively (no Docker). Read before changing an established approach.
- `formats.kb/` — reference for the on-disk formats we parse (VPK v2 container,
  Source 2 compiled `_c` resources, KV3) and the asset-type/extension inventory.
- `environment.kb/` — facts about this host and the game install that the code
  depends on (game-install paths, host Alpine/musl + gcompat quirks, the pinned
  toolchain).
