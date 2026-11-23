---
label: DATALOG_DECLINED
standing: agent
why:
- relational-discipline-is-right.md
---

# A Datalog engine is declined

Datalog is weak at floating-point aggregation, time series and
anything simulation-shaped, and adds a language with poor Python
interop. The one good fit is compile's modifier and stacking rules,
where provenance matters, and pure Python with provenance records
gets that without the engine (`provenance-records.md`). Revisit only
if those rules grow large.
