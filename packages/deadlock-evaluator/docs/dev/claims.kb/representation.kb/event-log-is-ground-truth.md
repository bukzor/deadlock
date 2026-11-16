---
label: EVENT_LOG
standing: agent
---

# The event log is the ground truth of a match

A match is its ordered event log: damage, kill, cast, purchase, soul
pickup, objective. Source 2 demos are already nearly this. Every other
representation is a fold over it, so parsers target the log and
nothing else, and a new view costs a fold, never a parser.
