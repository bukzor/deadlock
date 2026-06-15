# Toolchain & pinned versions

- **Python:** managed CPython via `uv`, pinned in `.python-version` (3.12).
  Recreate the venv with `uv venv --python 3.12 && uv sync`. lz4 (a
  `keyvalues3` dep) compiles from source on musl — the managed interpreter
  bundles the headers needed.
- **Type/test:** `pyright` (strict) and `pytest` (with `--doctest-modules`), run
  via `./bin/shell`.
- **Build:** `redo` (apenwarr, 0.42d) for regenerating `data/`.
- **ValveResourceFormat — pinned to 19.2.** Vendored at
  `data/tools/Source2Viewer-CLI` (glibc `cli-linux-x64`, runs natively here).
  Reports `Version: 19.2.6339`. Upstream warns CLI flags aren't stable across
  releases — re-check `--help` after any bump, and keep this pin in sync with
  whatever `s2v.py` / the fetch script downloads.

External library deps (`vpk`, `keyvalues3`) are pinned in `uv.lock`; the
reasoning for each is in `../decisions.kb/reuse-existing-parsers.md`.
