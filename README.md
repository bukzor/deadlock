# deadlock

Deterministic, repeatable parsing/inspection of the Deadlock (Source 2) game
binary, to:

- diff patch changes precisely (`git diff` after each patch shows exactly what
  Valve changed),
- understand game mechanics from data, not black-box play,
- view assets (models, textures, audio) locally.

## How it works

Python parsers (`src/deadlock/`) read the game's VPK archives and decompiled
KV3 resources, flatten them to sorted, line-oriented JSONL, and derive TSV
views. `redo` orchestrates regeneration; outputs land under `data/`. See
`docs/dev/` for the format references and design decisions.

```sh
./bin/shell pytest    # run everything through the project environment
redo                  # regenerate data/ from the local game install
```

Requires a local Deadlock install (paths in
`docs/dev/environment.kb/game-install-paths.md`).

## About the committed game data

`data/gamedata.flat/` and `data/manifest.jsonl` contain data extracted from
Deadlock — ability/hero/item stats and a file manifest. That data is Valve's;
committing it is what makes patch-over-patch diffing work, and is this repo's
reason to exist.

This follows long-standing, Valve-tolerated prior art: SteamDB, the Deadlock
community wikis, deadlock-api, and many other datamining projects have
published this class of derived stat data for years. No playable assets
(models, textures, audio) are committed — extraction of those stays local and
gitignored.

If you're from Valve (or otherwise have a stake) and want any of this data
removed or handled differently, open an issue — happy to discuss and quick to
comply.

## License

The code is licensed under [Apache-2.0](LICENSE). The extracted game data
under `data/` is not covered by that license; it remains Valve's property.
