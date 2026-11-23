---
label: ARCHITECTURE
standing: agent
ontology:
- layer
- Build
- Situation
- Outcome
- StatVector
- compile
- economy
- engage
- observe
- measure
- aggregate
- attribute
- pareto
why:
- goals.md
stale-when: a goal needs a component that is not a composition of these
---

# architecture -- layers, schemas, components

The evaluator is a tower of layers cut by what each layer knows, three
shared schemas that are the layers' only interface, one evaluator type
with three implementations, and a handful of generic operators. Each
goal is a short composition of components. The owner's reaction to the
first statement of this:

> [!@bukzor] cd601ea7#L107
> excellent. That's a great start.

and, on the Situation schema specifically, a critique that this theory
has absorbed:

> [!@bukzor] cd601ea7#L107
> 'situation' is a snapshotted simplification of a limited time and space of a game. Given that we'll want to (eventually) predict transitions between 'situations' and/or derive a 'situation' from a replay, is that the representation we want?
