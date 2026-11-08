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
- Generated output goes under `data/` and is regenerated with `redo`. Only the
  transformative TSV views and the build stamp are committed; the raw extracts
  (flats, manifest), assets, and vendored tools are gitignored — never commit
  them.

## Knowledge bases

The design, decisions, and reference knowledge live in `docs/dev/`. Read
`docs/dev/CLAUDE.md` before acting: it says which knowledge base to read when,
and how to write docs there.
