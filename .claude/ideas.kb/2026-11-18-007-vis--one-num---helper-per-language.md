---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: one num() helper per language

## The Idea

Five numeric-coercion helpers with five semantics: `guns._num`/`_given`, `melee._num(value, *where)`, `casts._number` (regex, raises `BadRequest`), `boons._stat`, `queries._number`; and `num()` twice on the client (`selection.ts:129`, `chart.ts:189`).

Smallest fix: one `num(value, *where) -> float` beside `dig` in `src/bukzor_deadlock/types.py`; one exported client `num` (e.g. in `format.ts`). `casts._number` and `queries._number` stay: they parse user input.

## Exploration Notes

Provenance (the handoff files are removed): Risk 3 of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md` at `2b797f3` (`git show 2b797f3:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
