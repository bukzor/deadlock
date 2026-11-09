# Toolchain & pinned versions

- **Python:** managed CPython via `uv`, pinned in `.python-version` (3.12).
  Recreate the venv with `uv venv --python 3.12 && uv sync`. lz4 (a
  `keyvalues3` dep) compiles from source on musl — the managed interpreter
  bundles the headers needed.
- **Type/test:** `basedpyright` (`all` mode; answers to `pyright` via the
  `basedpyright-as-pyright` shim) and `pytest` (with `--doctest-modules`), run
  via `./bin/shell`.
- **Build:** `redo` (apenwarr, 0.42d) for regenerating `data/`.
- **ValveResourceFormat — follows the latest release.** The pin (version +
  sha256) is the committed `data/tools/vrf-release.json`, which `redo` refreshes
  from the GitHub API at most daily (via `data/date.txt`); a new release
  re-provisions `data/tools/Source2Viewer-CLI` (fetch: `bin/fetch-vrf`) and
  re-extracts, and the bump shows in `git diff` beside the data it changed.
  The glibc `cli-linux-x64` build runs natively here.
  `deadlock.s2v.binary_path` resolves the binary (override `DEADLOCK_S2V`).
  Upstream warns CLI flags aren't stable across releases — if extraction breaks
  after a bump, check `--help` against `s2v.py`.

External library deps (`vpk`, `keyvalues3`) are pinned in `uv.lock`; the
reasoning for each is in `../decisions.kb/reuse-existing-parsers.md`.
