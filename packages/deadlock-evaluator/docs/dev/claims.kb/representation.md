---
label: REPRESENTATION
standing: agent
ontology:
- event log
- macro state
- episode
- decision stream
- win probability added
- breakpoint lattice
- soul-time
- archetype
why:
- architecture.md
stale-when: a view the applications need that no fold over the event log yields
---

# representation -- how a match is written down

A match is an event log; everything else is a derived view of it. Four
views serve the goals: the macro-state path, typed episodes, per-player
decision streams, and the fight entry summaries the architecture calls
Situations. Two constructions give the views a common scale: win
probability added as the currency, and soul-time as the clock. Two more
cut the fast layer into pieces: the breakpoint lattice and archetypes.
The owner's question that shaped this:

> [!@bukzor] cd601ea7#L107
> Will it be tractable to represent a whole replay as a series of 'situations', for example?

The answer this theory gives is no, and that a replay is the event log
with Situations as one of several views.
