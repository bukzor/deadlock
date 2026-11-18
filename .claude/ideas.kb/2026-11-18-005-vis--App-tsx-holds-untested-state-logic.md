---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: App.tsx holds untested state logic

## The Idea

`apps/vis/client/src/App.tsx` is the one untested client module and holds the trickiest logic: `baseOf` (line ~160), the `periods` memory of a cycle's period across horizon edits (~52-54), `splitTimeline`, and `useLines`' stale-answer guard. A second view will copy it.

Smallest fix: move `baseOf`, the period memory and `splitTimeline` into `selection.ts` (or a `timeline.ts`) with vitest cases; `App.tsx` keeps only JSX and hooks.

## Exploration Notes

Provenance (the handoff files are removed): Risk 1 of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md` at `2b797f3` (`git show 2b797f3:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
