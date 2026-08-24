---
status: accepted
date: "2026-08-24"
---

# Machine-local paths live in `localhost.env`, not in the code

`deadlock.paths` exposes exactly one install knob, `DEADLOCK_HOME` — the install
root, i.e. what Steam's "Browse local files" opens. Everything else
(`game/`, `citadel/`, `pak01_dir.vpk`, `steam.inf`) is derived from it. Its
committed default is the stock native-Linux Steam library,
`~/.local/share/Steam/steamapps/common/Deadlock`. Per-machine reality goes in
`localhost.env` at the repo root: gitignored, `watch_file`d, and loaded by the
*last* line of `.envrc` so it wins over anything the file sets.

## Why

The committed default used to be
`/mnt/c/Program Files (x86)/Steam/steamapps/common/Deadlock/game` — this
maintainer's WSL-through-Windows install, hardcoded in the module and asserted
by its test. That is a fact about one box sitting in shared source: a clone
elsewhere silently resolves nothing, and the test enshrines the wrong thing as
"the default".

Splitting it in two keeps each fact where it can be true: the *shape* of a stock
install is committed; the *actual* path is machine-local. `localhost.env` also
generalizes — any future host-specific setting goes there rather than accreting
another committed default.

`DEADLOCK_HOME` replaced `DEADLOCK_GAME_DIR` (one level deeper) because `game/`
is a Source 2 layout detail we know and the user does not; the install root is
the directory a person can actually point at. One knob, no alias.

## Alternatives weighed

- **Probe an ordered candidate list** (native → flatpak → `/mnt/c`), first that
  exists. Rejected: resolution would depend on filesystem state, weakening the
  module's promise of deterministic paths, and it still guesses.
- **Keep the default in `.envrc`.** Rejected: `paths.py` needs a default anyway
  for non-`direnv` use, and the same path string in two files invites drift.
  `.envrc` therefore contributes *no* default — only the override hook.
- **`.env`** as the filename. `localhost.env` is not a dotfile, so `ls` finds
  it, and the name says *why* it's uncommitted.

## What would change this

Deadlock shipping a native Linux build (today every real install is Proton or
Windows-through-WSL, so the committed default is a sane shape rather than a path
that is often right), or a second machine-local knob appearing — at which point
check that `localhost.env` is still loaded late enough to override it.
