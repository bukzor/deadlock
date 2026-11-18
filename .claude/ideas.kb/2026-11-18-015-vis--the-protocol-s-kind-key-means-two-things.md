---
managed-by: Skill(llm-subtask)
status: open
cost-benefit-sweh:
  timebox:
    "@value": 0.5  # SWEh worth exploring before promoting or abandoning
  benefit-2w:
    "@value": 1.0  # SWEh value created over 2w if this pans out
---

# vis: the protocol's kind key means two things

## The Idea

`kind` names two unrelated things in one protocol. On an `abilities` line it
is the damage source (`gun` / `melee` / `cast` / `null`); on a `timeline`
line it is the line's type (`hit` / `cycle` / `measure` / `note`). So `jq
.kind` means something different depending on the query, and the client
passes both around as `kind` (`AbilityKind`, `TimelineLine.kind`). The
server already calls the first one a source (`queries.Source`, `_source`).

Smallest fix: rename the `abilities` field to `source`, and `Kind` /
`AbilityKind` to match. The line-type tag keeps the name `kind`.

## Exploration Notes

- Do it together with idea 010 (one JSON Schema for both languages): the
  schema's tagged lines fix the tag's name, so the rename costs one pass
  instead of two.
- The rename reaches `docs/dev/decisions.kb/vis-app.md` (Protocol table), the
  README's `jq` examples (`select(.kind)` on `abilities`), and claims that say
  `kind` (`grep -rl kind apps/vis/docs/dev/claims.kb`).
- Surfaced by a review of `apps/vis` on 2026-11-18 (session 380c3ab7); the
  agent's suggestion, not ruled on.

## Next Steps (if pursuing)

- [ ] Rename in the schema (idea 010), or in `queries.py` + `protocol.ts` if 010 isn't taken up.

## Lifecycle

**Status:** Exploring | Promoted to todo.kb/2026-11-18-NNN-title.md | Abandoned (see ADR/reasoning)
