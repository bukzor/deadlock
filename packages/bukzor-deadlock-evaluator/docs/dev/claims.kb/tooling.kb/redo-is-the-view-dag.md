---
label: REDO_DAG
standing: agent
why:
- relational-discipline-is-right.md
---

# redo is the build DAG over derived views

Each derived view is a `.do` target, exactly as the parent project
regenerates its data. This is the incremental-maintenance half of what
Datalog promises, already in the repo's habits.
