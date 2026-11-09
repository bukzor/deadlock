---
managed-by: Skill(llm-subtask)
status: open
---

- [ ] <https:todo.kb/2026-11-05-000-per-dll-dump-tree.md> — per-DLL data store, first purpose the convar/concommand dump: `dlls.list` → `dlls/<facet>/<dll>.json` → `dlls/<facet>.tsv` (design: `docs/dev/convar-dump.kb/output-views.md`)
- [x] Have redo handle VRF updates, the way `data/deadlock-version.json` tracks game patches: today the pin (`VERSION`/`SHA256`) is hardcoded in `bin/fetch-vrf`, and only a hand edit re-provisions `data/tools/Source2Viewer-CLI.d`
  - [x] Why now: pinned 19.2 can't read build 6851 (`UnexpectedMagicException: Unknown KVType for variable 'datatype': 26 (0x1A)` on `scripts/heroes.vdata_c` and `.vcss_c`), so gamedata is stuck at 6731 (Oct 1); latest is 20.1 (2026-10-15)
  - [x] New committed target `data/tools/vrf-release.json`, rechecked daily via `data/date.txt` (`redo-always` + `redo-stamp`), over `gh api repos/ValveResourceFormat/ValveResourceFormat/releases/latest`, recording the tag and `cli-linux-x64.zip`'s `digest` (sha256) — the stamp keeps it from invalidating anything until the release actually changes
  - [x] `bin/fetch-vrf` reads version + sha from that file instead of hardcoding; `Source2Viewer-CLI.d.do` `redo-ifchange`s it, so a new release re-provisions, and the bump shows up in `git diff` beside the gamedata it changes
  - [x] Decided: `all.do` follows latest -- it reaches `vrf-release.json` via `gamedata.list` → CLI, and adopts it as committed. Risk: VRF doesn't promise CLI flag stability (`s2v.py` docstring), so a bump can break extraction
  - [x] Update `docs/dev/environment.kb/toolchain.md`; provisioned 20.1
  - [x] Run `redo` to re-extract with 20.1 (landed on 6854, Nov 05); flags held. `weapons.py` profile check narrowed to live primaries (`ability_nurse_fear`, `ability_ratking_scrap_grenade` carry extra profiles)
- [x] Convert the remaining flat-path regex modules to `flatten.tree` (nested dicts), following `weapons.py`; fix each module's stale "committed, flattened" docstring (flats are local-only) as it's touched
  - [x] `items.py` (`_PRICE`, `_ENTITY`, `_COMPONENT`)
  - [x] `levels.py` (`_PATH`)
  - [x] `abilities.py` (`_BOUND`, `_DISABLED`, `_PROP`)
  - [x] `item_bonuses.py` (`_ENTITY`, `_PROP`)
  - [x] `ability_upgrades.py` (`_ENTITY`, `_UPGRADE`)
  - [x] `heroes.py` (`_PATH`, `_ATTR`)
  - [x] `weapons.py` docstring only (already converted)
- [ ] Think through a revamp of validation and error handling: assert wherever a change would make output quietly wrong or trivial, handle (normalize, blank cell) wherever it is merely different
  - [ ] Leading design to test: creation stays lenient and total; judgment moves to separate redo targets that write findings as data (`data/gamedata.check/<subject>.findings.tsv`, one row per violation, empty when clean), and `all.do` fails if any are non-empty (redo discards a failed target's output, so a failing check leaves nothing to inspect)
  - [ ] Two subject kinds: source-shape checks (depend on the game-data JSON only) and view-output checks (depend on the view's TSV: empty table, all-blank column)
  - [ ] Inventory every assertion and special case in `src/deadlock/` and sort it: our own parser is wrong (stays in creation) / quiet-wrongness canary (becomes a finding) / over-specific (handled)
  - [ ] Known gaps to cover: signature slot-prefix rename gives an empty table silently; `m_bDisabled` can serialize as bool/`"true"`/`1` (`items._truthy` normalizes, heroes/weapons do not); renamed `m_strValue`/`AbilityCooldown` gives all-blank cooldowns; renamed `EAbilityPoints` gives an all-zero AP column; a blank hero stat is ambiguous (hero-unique vs dropped) but decidable via `_base`: assert a hero's stats are a superset of its `_base`'s (check what `_base` holds, and whether chains exist)
  - [ ] Pre-commit gap: building a single view directly skips the gate; decide whether a pre-commit step runs it
- [ ] Reading views over `data/dlls/`: `load.tree.txt` and `concommands.md` (local-only outputs of `deadlock.dlls_{load_tree,concommands_md}`)
  - [ ] Once 020 lands `convars.tsv`: one `console.md` help page over convars and concommands together, a convar item adding its type, default and min/max (supersedes `concommands.md`)
  - [ ] `all.do` builds neither view, so they go stale; add them to its `redo-ifchange`

## Later

- [ ] `data/dlls/load.edges.tsv` (`loader<TAB>loaded`, one inferred edge per line) as the diffable form of the load graph: one changed dependency is one changed line, where `load.tsv`'s closure cells change on every DLL above it; `load.tree.txt` and an inverted (`what loads X`) tree render from it
  - [ ] Hoist each shared subtree (loaded by ≥2, loads something) to its own root, so every `(*)` points at a root rather than wherever the sort first drew it
- [ ] `redo-trace --all` (`packages/bukzor-redotools`): every root log on the real clock, one Perfetto track each — the latest known cost of every target. The default (the newest build) is often a no-op `redo all`; on 2026-11-09 the real timings sat in 318 separate root logs
- [ ] `redo-trace --open`: serve the trace once to ui.perfetto.dev (its CSP allows `http://127.0.0.1:9001`; send `Access-Control-Allow-Origin: *`; 404 its `POST /status` trace_processor probe, then exit after the `GET`) and `wslview 'https://ui.perfetto.dev/#!/?url=http://127.0.0.1:9001/trace.json'` — prototyped and working by hand
