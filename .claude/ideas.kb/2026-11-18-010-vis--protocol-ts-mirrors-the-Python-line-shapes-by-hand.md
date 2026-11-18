---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 2.0  # SWEh value created over 2w if this pans out
---

# vis: protocol.ts mirrors the Python line shapes by hand

## The Idea

`apps/vis/client/src/protocol.ts` restates the server's line shapes (`types.py`) by hand and nothing checks the two against each other; a server field change breaks the client silently.

Smallest fix: generate the TypeScript from the Python types, or a test that runs every query against real data and validates the lines against the TS shapes (or a JSON Schema both sides read).

## Exploration Notes

Provenance (the handoff files are removed): A risk the coordinator of the vis-app plan found while writing 029; it has no handoff-file source (`git show 53e22d0:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-029-future-improvements.md`).

## Next Steps (if pursuing)

- [ ] Do the smallest fix above.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
