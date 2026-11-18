---
managed-by: Skill(llm-subtask)
status: open
blocked-by: []
required-reading:
  - ./CLAUDE.md   # the protocol only; you change no code
  - ../../../CLAUDE.md   # the repo's standards
  - ../../../apps/vis/
  - ../../../docs/dev/decisions.kb/vis-app.md
---

# Tech advisor: how maintainable is `apps/vis`?

**Parent:** <https:../2026-11-18-000-vis-app.md> (wrap-up)

## Problem Statement

The user asked for a second opinion, as impartial as possible, from a "tech
advisor" on the maintainability of `apps/vis`: its source, tests, tooling and
docs. It was built today, by several agents, in about two hours.

Form your own view from the code. Judge what a developer who is new to the
repo would face when they come to change it in six months, for example to add a
second view or a new kind of damage source, or to follow a game patch. Weigh
it against common practice for a project of this size, not against perfection.

**Deliverable**, in this file's Final report:

- an overall rating out of 10, with the reasoning for it;
- strengths and risks, each pointing at files, ranked by how much each one
  affects the cost of future change;
- for each risk, the smallest change that would address it.

Findings only; edit nothing but this file. Units 026 and 027 are editing the
server and client in parallel; review what is committed (`git show HEAD:…`
if a file is mid-edit).
