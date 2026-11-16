---
label: EVALUATOR
standing: agent
ontology:
- evaluator
- game data
- replay
- player
non-claim-tokens:
- S1
- TTK
- DPS
- HP
- API
- SQL
- JSON
- DP
- MOBA
- GLM
- RL
- L0
- L1
- L2
- L3
- L4
- L5
- CTE
- TSV
- VPK
- DAG
- L83
- L98
- L107
- L126
stale-when: the deadlock package stops being the source of game data, or the goals
  theory is rewritten
---

# The evaluator's design, as a ledger

The deadlock-evaluator turns game data and replays into judgments about
a player's build decisions. This ledger records what that design
commits to, in `Skill(llm-claims)`'s notation: one claim per file, each
carrying its label and its standing. It was extracted from one design
conversation (session `cd601ea7`, 2026-11-16) and is mostly `agent`-signed:
the owner set the goals and approved the direction in passing, and has
ruled on little else yet.

> [!@bukzor] cd601ea7#L107
> excellent. That's a great start.

> [!@bukzor] cd601ea7#L126
> This sounds great. But I see exponential, factorial explosion lurking between the lines in many spots here.

Those words endorse a direction, not any one claim. They are quoted
here so a reader knows the tone of the approval and does not mistake an
`agent` claim for a ruling.

## Theories

```
goals ──► architecture ──► representation ──► tractability
                                    └──────► tooling
```

| Theory | Holds | Stale when |
|---|---|---|
| `goals` | what the owner wants answered, and the goals an agent proposed adding | the owner names a goal none of these serve |
| `architecture` | the layers, the three schemas, the evaluator interface, the components and their compositions | a goal needs a component that is not a composition of these |
| `representation` | how a match is represented: event log, derived views, the common currency, the lattice | a view the applications need that no fold over the event log yields |
| `tractability` | the one principle and four tactics that cut the combinatorial sites | an explosion site none of the four tactics cuts |
| `tooling` | the data technologies chosen and declined | a corpus the chosen store cannot hold or query |

The chain runs one way: a goal is stated before the architecture that
serves it, a representation before the tactic that compresses it, and a
tool is picked last, for a representation already chosen.

## Standing

```bash
grep -rH '^standing:' claims.kb/ | sort -t: -k3        # every claim, by judge
grep -rl 'standing: open' claims.kb/                    # asks: what would settle each?
grep -rl 'standing: agent' claims.kb/                   # the owner's veto queue
grep -rl 'verdict:' claims.kb/                          # struck claims
```

The `agent` set is the one to sweep: each entry is a judgment made on
the owner's behalf. The `open` set is small and names the facts to go
measure first.
