---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: horizon inputs follow the hp zoom

## The Idea

With `hp` set, the server zooms the horizon out to the kill (the `cycle` line carries it), but the client's horizon inputs still show the typed value while the chart spans the zoomed horizon.

Smallest fix: show the effective horizon as the input's placeholder (or value), from the `cycle` line, in `apps/vis/client/src/App.tsx`.

## Exploration Notes

Provenance (the handoff files are removed): Open Questions of `.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-026-names-and-hp-zoom.md` at `85f36ff` (`git show 85f36ff:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-026-names-and-hp-zoom.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
