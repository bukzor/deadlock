---
label: TOOLING
standing: agent
why:
- representation.md
stale-when: a corpus the chosen store cannot hold or query
---

# tooling -- data technologies chosen and declined

The owner smelled Datalog in the derived-view structure and asked
whether it, or any data technology, pays for itself over JSON and
in-memory Python.

> [!@bukzor] cd601ea7#L126
> a lot of this 'views on relations' smacks of datalog, to me. Do you smell that, too? Would datalog be helpful here? Or more cost than benefit? ... are there any particular data technologies that would be helpful as building blocks here? or is json+python in-memory Good Enough (tm)?

The answer: the relational discipline is right and a Datalog engine is
not; SQL over a columnar store supplies most of the benefit; JSON and
Python suffice everywhere except the replay corpus.
