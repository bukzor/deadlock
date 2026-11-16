---
label: RELATIONAL_DISCIPLINE
standing: agent
why:
- ../representation.kb/event-log-is-ground-truth.md
---

# The relational discipline is right

Everything downstream of the event log is derived relations over base
facts, with joins across game data, replays and builds. The Datalog
smell is accurate: declarative derived views, incremental
recomputation and provenance are the properties wanted, and the
design keeps them whatever engine runs the views.
