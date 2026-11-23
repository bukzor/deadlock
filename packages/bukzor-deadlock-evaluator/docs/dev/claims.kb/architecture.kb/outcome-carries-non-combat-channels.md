---
label: OUTCOME_CHANNELS
standing: agent
why:
- three-schemas-are-the-base.md
- ../goals.kb/non-combat-value.md
---

# Outcome carries non-combat channels

An Outcome records damage traded, time-to-kill, kill or not, resources
spent, and also souls gained and objective damage. Putting the economic
channels in the schema means a duel simulator that ignores them
returns zeros a reader can see, rather than silently pricing mobility
and farm items at nothing. Summary statistics only, pending
`outcome-trace-or-summary.md`.
