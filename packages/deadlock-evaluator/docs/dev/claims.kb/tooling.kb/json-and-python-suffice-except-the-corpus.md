---
label: JSON_PYTHON_LIMIT
standing: agent
why:
- event-volume-per-demo.md
---

# JSON and in-memory Python suffice everywhere but the replay corpus

Game data, compile and engage fit comfortably in plain Python. A
replay corpus does not: one match is on the order of half a million
position and damage events, so a thousand matches as Python dicts
will not fit in memory, and the derived views need joins and windows
over all of them. The estimate is `event-volume-per-demo.md`; if it is
off by an order of magnitude downward, this claim weakens.
