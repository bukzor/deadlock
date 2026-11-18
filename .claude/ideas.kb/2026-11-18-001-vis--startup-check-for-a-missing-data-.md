---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: startup check for a missing data/

## The Idea

A server started without `data/` (built by `redo`) answers a bare 500 in the browser. Evidence: no `redo` hint anywhere in `apps/vis/server/src/vis_server/` outside tests; only the real-data tests name it when they skip.

Smallest fix: check `data/gamedata.json` at startup in `__main__.py`/`http.py`, and exit (or answer) with a message naming `redo`.

## Exploration Notes

Provenance (the handoff files are removed): `.claude/todo.kb/2026-11-18-000-vis-app.md` "Later" list at `53e22d0` (from unit 012 (`2026-11-18-012-end-to-end.md`)).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
