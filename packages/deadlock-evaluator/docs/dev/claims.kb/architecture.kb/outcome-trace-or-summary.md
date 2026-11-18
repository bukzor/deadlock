---
label: OUTCOME_TRACE
standing: agent
why:
- goals-are-compositions.md
---

# Outcome is summary statistics; a trace is an additive field

Outcome carries summary statistics only (damage traded, time to kill,
kill or not, resources spent, souls gained, objective damage). Every
composition listed consumes summaries. A per-tick trace, if attribute
ever needs to say *when* in a fight a stat mattered, is added as an
optional field: it never invalidates a summary-only consumer, so the
decision costs nothing to defer and nothing to reverse.
