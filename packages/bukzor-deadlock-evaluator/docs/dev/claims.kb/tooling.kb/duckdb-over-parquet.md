---
label: DUCKDB_PARQUET
standing: agent
why:
- relational-discipline-is-right.md
- json-and-python-suffice-except-the-corpus.md
---

# DuckDB over Parquet holds the event log and every derived view

Zero server, reads the parent project's TSVs directly, excellent
numerics, native Python and pandas interop. Views are declarative,
joins are cheap, window functions do the event-fold, and recursive
CTEs cover the few recursive bits. This supplies most of what a
Datalog engine would, and is the one new storage dependency.
