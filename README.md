---
last-updated: 2026-06-15
---

# deadlock

Deterministic, repeatable parsing/inspection of the Deadlock (Source 2) game
binary. Three uses:

1. **Diff patches precisely** — commit the generated data, regenerate after a
   patch, read `git diff`.
2. **Understand mechanics from data** — heroes/abilities/modifiers as flat JSONL.
3. **View assets** — decompile textures/models/audio to png/glTF/wav.

Built on existing tools (no reinvention): [`vpk`] for the archive layer,
[`keyvalues3`] for KV3, and [ValveResourceFormat]'s `Source2Viewer-CLI` for
decompilation. See `docs/dev/decisions.kb/` for why.

## Setup

```sh
uv sync                 # managed CPython + deps
./bin/fetch-vrf         # vendor the pinned Source2Viewer-CLI into data/tools/
```

Run tooling through the env wrapper: `./bin/shell pytest`, `./bin/shell pyright`.
Game paths default to a WSL Steam install; override with `DEADLOCK_GAME_DIR`.

## Generating data

`redo` produces everything under `data/` (regenerated correctly when the source
VPK or the parser changes):

```sh
redo all                    # rebuild every committed leaf below

redo data/manifest.jsonl    # one file per line: {path, crc32, size}
redo data/gamedata.jsonl    # one game-data leaf per line: {file, path, value}
```

From `gamedata.jsonl` we also compile focused, diff-friendly mechanics tables:

```sh
redo data/levels.tsv        # player level/souls/ability-point curve
redo data/heroes.tsv        # wide per-hero base stat sheet (one hero per row)
redo data/items.tsv         # shop economy: tier, resolved soul cost, slot, components
redo data/abilities.tsv     # each live hero's four signature abilities
redo data/weapons.tsv       # each live hero's primary weapon (+ derived DPS)
redo data/item_bonuses.tsv  # the passive stat bonuses each shop item grants
redo data/ability_upgrades.tsv  # what each signature ability's 3 upgrades do
```

All are committed and line-grained, so a patch's changes show up as a clean
`git diff`. To inspect a patch: update the game, re-run the `redo`s, `git diff`.

## CLI entry points

```sh
python -m deadlock.manifest [vpk]                 # VPK manifest as JSONL
python -m deadlock.gamedata <file.vdata> ...      # KV3 -> flat leaf JSONL
python -m deadlock.extract [--gltf] <dir> [ext…]  # extract+decompile assets

python -m deadlock.levels    data/gamedata.jsonl  # level/souls/AP curve TSV
python -m deadlock.heroes    data/gamedata.jsonl  # per-hero base stat sheet TSV
python -m deadlock.items     data/gamedata.jsonl  # shop item economy TSV
python -m deadlock.abilities data/gamedata.jsonl  # hero signature abilities TSV
python -m deadlock.weapons   data/gamedata.jsonl  # hero primary weapon stats TSV
python -m deadlock.item_bonuses data/gamedata.jsonl # per-item stat bonuses TSV
python -m deadlock.ability_upgrades data/gamedata.jsonl # ability upgrade tiers TSV
```

Assets are bulk/binary and **extracted on demand** into gitignored `data/`
(not committed). Examples:

```sh
python -m deadlock.extract --gltf data/assets vmdl_c   # models -> .glb
python -m deadlock.extract data/assets vtex_c          # textures -> .png
python -m deadlock.extract data/assets vsnd_c          # audio -> .wav/.mp3
```

## Layout

- `src/deadlock/` — modules (≤300 lines each) with `{module}_test.py` alongside
- `docs/dev/*.kb/` — decisions, format reference, environment facts
- `data/` — generated output (mostly gitignored; the JSONL artifacts are tracked)

[`vpk`]: https://github.com/ValvePython/vpk
[`keyvalues3`]: https://github.com/kristiker/keyvalues3
[ValveResourceFormat]: https://github.com/ValveResourceFormat/ValveResourceFormat
