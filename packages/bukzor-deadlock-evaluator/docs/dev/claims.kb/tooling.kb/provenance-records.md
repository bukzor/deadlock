---
label: PROVENANCE_RECORDS
standing: agent
why:
- ../architecture.kb/compile-is-pure-and-emits-breakpoints.md
---

# compile outputs carry provenance fields

Each stat in a StatVector is a dataclass with the modifiers that
produced it, so attribute can say why a stat has its value without a
rules engine. This is the Datalog provenance property, done in Python.
