---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: pin casts.py's survey counts to its docstring

## The Idea

`casts.py` carries ~15 raw vdata property names and fitted fallback lists (`_DURATIONS`, `_TICKS`); a field renamed by a patch is an `AssertionError` 500 with no body. Its docstring survey ("99 of 184 bound ...") is checked only as `> len(bound)/3` in `casts_test.DescribeRealData`, so the heuristic can drift silently.

Smallest fix: tighten that test to the survey's exact counts, so a patch fails it and points at the docstring to refresh.

## Exploration Notes

Provenance (the handoff files are removed): Risk 2 of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md` at `2b797f3` (`git show 2b797f3:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
