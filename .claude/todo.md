---
managed-by: Skill(llm-subtask)
status: open
---

- [ ] `packages/deadlock-evaluator` design ledger (`docs/dev/claims.md` there): owner rulings parked 2026-11-18, each a short read; the agent-filed answers stand until vetoed
  - [ ] Review the closed plan `docs/dev/close-open-claims.md` (commits 2041c59..) and say so; then its `close-open-claims.kb/` gets `git rm -r`'d
  - [ ] Ground `claims.kb/goals.kb/`: six files carry `standing: user` with no quote of yours (base-before-branches, build-synthesis, dominated-decisions, explain-popular-builds, item-choice, skill-point-choice); confirm or reword. Eight agent-standing goals stand unless vetoed
  - [ ] Veto or let stand two agent rulings: `architecture.kb/outcome-trace-or-summary.md` (summary stats, per-tick trace optional) and `architecture.kb/micro-policy-is-the-open-input.md` (scripted per-hero rotation first, calibrated against live measurement later)
  - [ ] Rule on the vis import edge (`architecture.kb/vis-timeline-seeds-compile-and-engage.md`): lift the timeline into the shared `deadlock` package, or move the evaluator into vis's 3.14 workspace
- [x] <https:todo.kb/2026-11-18-000-vis-app.md> — `apps/vis`: browser visualizer over `data/` (client + JSONL server); first view: damage over time per hero ability
- [ ] <https:todo.kb/2026-11-05-000-per-dll-dump-tree.md> — per-DLL data store, first purpose the convar/concommand dump: `dlls.list` → `dlls/<facet>/<dll>.json` → `dlls/<facet>.tsv` (design: `docs/dev/cvar-dump.kb/output-views.md`)
- [x] Deterministic, fail-loud DLL scan: decisions made 2026-11-11 on the agent's recommendation, open to review; each is a `[!TODO]` with its "what would change this" in its doc
  - [x] Allocator hook locates every DLL's queues but tier0's; then drop `learn_strides` and `data/dlls.check/strides` (`docs/dev/cvar-dump.kb/capture-approach.kb/allocator-hook.md`)
  - [x] Pin the Windows interpreter: uv-managed CPython, exact version, in `bin/winpy` (`docs/dev/cvar-dump.kb/windows-python-host.md`)
  - [x] `load` lists only added modules whose files are in the install (`docs/dev/cvar-dump.kb/dll-coverage.md`)
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
- [ ] Reading views: `data/dlls/load.tree.txt`, `data/concommands.md`, `data/convars.md` (local-only outputs of `deadlock.dlls_{load_tree,concommands_md,convars_md}`; the help pages share `deadlock.dlls_md`)
  - [ ] `all.do` builds none of them, so they go stale; add them to its `redo-ifchange`
- [ ] Format all Python with black + isort (`profile = "black"`), as in `bukzor-tools` (the user's lean, 2026-11-18). Line length 88, black's default and `bukzor-tools`' (the agent's call; 120 is the cheap alternative, see the survey below): a dev dep in the root and `apps/vis/server` workspaces, run as one reformat-only commit. Replaces the `ruff` in `ideas.kb/2026-11-18-008-vis--lint-and-a-one-command-check.md`
  - [ ] black can't parse `src/deadlock/ability_profiles_test.py` ("Unable to match a closing bracket"); find the construct and fix it first
  - [ ] Surveyed 2026-11-18: at 88 columns black reformats 115 files and pushes 8 past the 300-line limit (at 120: 74 files, only `queries.py` and `queries_test.py`). Split the others as the `queries.py` item below does: `casts_test.py`, `measures_test.py` (vis), `src/deadlock/cvarlist_check{,_test}.py`, `src/dllscan/registry.py`, `docs/dev/probes/hook_probe3.py`
- [ ] Split `apps/vis/server/src/vis_server/queries.py` (278 lines, 368 after black) into modules ≤300, and `queries_test.py` (306, already over; 448 after black) to match, a `_test.py` beside each new module. Do this after black, and measure after formatting. Natural seams: the parameter parsing (`_required`, `_number`, `_optional_number`, `_level`), the hit guard (`MAX_HITS`, `_starts`, `max_horizon`, `_check_hits`), and data loading (`GameData`, `load_data`, `listed`), leaving the registry and the three queries
- [ ] pnpm is on PATH only in interactive zsh (`~/prefix/pnpm/bin`), so `./bin/shell pnpm …` and the Bash tool fail: `apps/vis/README.md`'s `pnpm exec` checks, and `bin/serve`'s install step when the lockfile is newer. Get it onto the non-interactive PATH (the shell profile, in dotfiles, or `.envrc`). Volta is no help here: its binary dies on this musl host (`Error relocating …/volta: __res_init: symbol not found`); worth a line in `docs/dev/environment.kb/host-alpine-musl-gcompat.md`. Workaround meanwhile: `apps/vis/client/node_modules/.bin/{tsc,vitest}`

## Later

- [ ] `data/dlls/load.edges.tsv` (`loader<TAB>loaded`, one inferred edge per line) as the diffable form of the load graph: one changed dependency is one changed line, where `load.tsv`'s closure cells change on every DLL above it; `load.tree.txt` and an inverted (`what loads X`) tree render from it
  - [ ] Hoist each shared subtree (loaded by ≥2, loads something) to its own root, so every `(*)` points at a root rather than wherever the sort first drew it
- [ ] `redo-trace --all` (`packages/bukzor-redotools`): every root log on the real clock, one Perfetto track each — the latest known cost of every target. The default (the newest build) is often a no-op `redo all`; on 2026-11-09 the real timings sat in 318 separate root logs
- [ ] `redo-trace --open`: serve the trace once to ui.perfetto.dev (its CSP allows `http://127.0.0.1:9001`; send `Access-Control-Allow-Origin: *`; 404 its `POST /status` trace_processor probe, then exit after the `GET`) and `wslview 'https://ui.perfetto.dev/#!/?url=http://127.0.0.1:9001/trace.json'` — prototyped and working by hand
- [ ] Commit `docs/games/` (untracked; Deadlock notes moved here by dotfiles reunify fold unit 004, 2026-11-10) once no peer session is live in this repo
