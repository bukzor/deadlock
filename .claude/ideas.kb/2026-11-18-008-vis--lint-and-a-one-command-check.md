---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: lint and a one-command check

## The Idea

No lint, no one-command check, no CI. `apps/vis/client/src/App.tsx:277` disables an eslint rule nobody runs; the README lists four check commands across two toolchains; `bin/serve` needs `pnpm` for install though vite runs from `node_modules/.bin`.

Smallest fix: `apps/vis/bin/check` (at most 50 lines bash) running both halves' checks; `ruff` in the `pyproject.toml` dev group with defaults.

## Exploration Notes

Provenance (the handoff files are removed): Risk 4 of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md` at `2b797f3` (`git show 2b797f3:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-028-maintainability-review.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
