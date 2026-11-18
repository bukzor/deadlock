---
label: VIS_APP
standing: agent
ontology:
- query
- pseudo-ability
non-claim-tokens:
- API
- DOM
- DPS
- JSONL
- KISS
- URL
- WSL2
- L5
- L1002
- L1273
- L1546
- L2963
- MODIFIER_VALUE_BASE_MELEE_DAMAGE_FROM_LEVEL
why:
- claims.kb/judge-on-own-authority.md
stale-when: the owner rules on the design in docs/dev/decisions.kb/vis-app.md, or
  withdraws the delegation
---

# apps/vis's judgement calls, as a ledger

`apps/vis` is built to a design at the repo root,
[`docs/dev/decisions.kb/vis-app.md`](../../../../docs/dev/decisions.kb/vis-app.md),
which says *what* is built. This ledger says which of those choices were
the agent's call, and why. The owner told the agent to make the open
calls on its own authority and to file each as an agent-signed claim
(`claims.kb/judge-on-own-authority.md`), so nearly every claim here is
`agent`: a decision in force, waiting on the owner's veto. The three
`user` claims are the owner's words the calls answer to: the request,
the delegation, and the acceptance bar. A **query** is a named entry in
the server's registry that answers JSONL lines; a **pseudo-ability** is
an entry in the `abilities` query that no ability in the data backs.

## Theories

```
VIS_APP ──► model
```

| Theory | Holds | Stale when |
|---|---|---|
| `VIS_APP` (here) | the owner's grounds; the stack, protocol and acceptance calls | the owner rules on the design |
| `model` | the calls inside the damage model, each overturned by an in-game measurement | a measurement disagrees with a timeline |

## Standing

```bash
grep -rH '^standing:' claims.kb/ | sort -t: -k3   # every claim, by judge
grep -rl 'standing: agent' claims.kb/              # the owner's veto queue
grep -rl 'standing: open' claims.kb/               # what to go measure
grep -rl '^todo: true' claims.kb/                  # decided, not yet built
grep -rl 'verdict:' claims.kb/                     # struck claims
```
