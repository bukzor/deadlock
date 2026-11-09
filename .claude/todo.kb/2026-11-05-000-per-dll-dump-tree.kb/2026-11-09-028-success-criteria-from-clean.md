---
managed-by: Skill(llm-subtask)
status: done
required-reading:
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.kb/CLAUDE.md
  - .claude/todo.kb/2026-11-05-000-per-dll-dump-tree.md
---

# Run the plan's success criteria from a clean tree

**Parent:** <https:../2026-11-05-000-per-dll-dump-tree.md> (Success Criteria)

## Problem Statement

Every step that builds the store has landed. Run each Success Criterion
that is still open on 6860, as stated, and report the evidence for each:
the command, its exit status, and the counts or diffs it rests on.

- "From clean" means the per-DLL documents and every target under
  `data/dlls/` and `data/dlls.check/` are gone first. Use `clean.do`'s
  mechanism, or remove exactly those targets: don't touch the gamedata
  extracts, which take long to rebuild and aren't part of this.
- Two consecutive builds byte-identical: the second from clean too, compared
  by sha256 over every document and TSV.
- The row counts: on 6860, from the committed TSVs and the queue counts the
  scanner reports. The criterion quotes 6854's numbers; give 6860's, and say
  whether they still hold.
- Also run `data/dlls.check/registry` once; it passed for 026.

This is a check, not a fix. If a criterion fails, stop, report the failure
with its output, and leave the code alone. Don't edit the plan.

**Scope:** no tracked file changes. Scratch in `trash/028/`. A sibling
(027) edits `docs/` concurrently.

## Steps

- [x] Install is 6860 (`game/citadel/steam.inf`); snapshot pre-state hashes
- [x] Clean (clean.do's DLL lines, `trash/028/clean-dlls.sh`), build 1, checks
- [x] Coverage and row counts (`trash/028/counts.py`), registry check
- [x] Clean, build 2, sha256 compare (`trash/028/hash.sh`); pytest, pyright

## Decisions

- Clean = exactly clean.do's DLL-store lines: `git clean -fdX -- data/dlls
  data/dlls.list data/dlls.check` (382 files) + `rm data/dlls/*.tsv` (4).
  That includes `dlls.list`, which clean.do treats as part of the store.
- After the criterion's command, a second `redo -j8` builds the rest of the
  store (`file.tsv`, `load.tsv`, `load.tree.txt`, the three `all.do` checks)
  so the hash covers every document and TSV.
- `registry` is excluded from the build-2 hash (run once per the brief), then
  re-run at the end to restore the local tree: same sha256 as its first run.

## Open Questions

## Final report

All open criteria hold on 6860. No tracked file changed.

| criterion | evidence |
|---|---|
| from clean, `redo -j8 data/dlls/convars.tsv data/dlls/concommands.tsv` exits 0 | build 1: exit 0, 2m13s real / 7m03s user+sys (≈3.2× parallel); built 97 `load`, 91 `convars`, 91 `concommands` atoms + 2 TSVs. Build 2: exit 0, 2m16s |
| every listed DLL has `load`; every `ok` has both documents | 97 listed, 97 `load` records: 91 ok, 4 excluded (assetpreview, helpsystem, propertyeditor, toolframework2), 2 failed `LoadLibraryExW: 126` (phonon4, vfx_dx11). 91 `convars` + 91 `concommands` docs, none missing, none extra |
| rows = queue counts, duplicates kept | convars 6223 rows = 6223 queue entries over 30 modules; concommands 1418 = 1418 over 30; 0 per-module mismatches. 6860 `server`: 2008 convars, 493 commands, the 6854 numbers unchanged (also `dlls.check/strides`). `client`: 2289 / 428. Duplicates kept: 40 (module, name) pairs repeat in convars.tsv (157 extra rows; 4 in server); none in concommands |
| two consecutive builds byte-identical | 385 files (all docs, 4 TSVs, `dlls.list`, `load.tree.txt`, 3 checks) sha256-identical between build 1 and build 2; both also equal the pre-clean tree, and `git diff data/dlls/` is empty (committed TSVs already 6860's) |
| `./bin/shell pytest`, `./bin/shell pyright` | 822 passed; pyright 0 errors, 0 warnings |
| `data/dlls.check/registry` (already ticked) | exit 0: server convars queue 2008 / registry 2003 / once 1999, all match; commands 493/493/493; client convars 2289 / 2234 / 2226, commands 428/428/428, all match |

Observation, not a failure: build logs print nested `redo` lines for source
files (`bin/winpy`, `src/dllscan/*.py`, game DLL paths), under redo 0.42d.
Logs and hashes: `trash/028/`.
