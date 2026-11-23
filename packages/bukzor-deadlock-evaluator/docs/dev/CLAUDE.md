# docs/dev (bukzor-deadlock-evaluator)

The design ledger, `claims.md` beside `claims.kb/`, kept per
`Skill(llm-claims-kb)`. Read `claims.md` first; it carries the theory poset
and the scan commands. `close-open-claims.md` beside `close-open-claims.kb/`
is the sub-agent plan that measures the ledger's open claims
(`Skill(subagent-handoffs)`).

## Telling settled from suggested

Every file carries `standing:`, and that field is the whole answer to
"is this decided?":

- `user` -- the owner ruled it; `authority:` cites where. Settled.
- `agent` -- an agent's proposal, veto invited. Silence is consent, but it
  is still not a ruling: never cite one as settled.
- `open` -- a question nobody has stood behind. Debt.
- `bare` -- a checkable fact (`verify:`) or something that follows from its
  `why:`. No judge needed.

A struck claim keeps its file and gains `verdict:`. Never delete a claim
to retract it. Never write a paraphrase in the owner's voice: the owner's
words appear only as `> [!@bukzor] <address>` callouts, quoted from the
session log or a commit.

## Where a new file goes

A claim goes under the theory whose coined words it needs; a theory is
a claim file beside the same-named collection directory. A claim needing words from two sibling theories
belongs downstream of both, or one of them wants a new shared prior. Run
the ledger tools from the skills workspace's venv, since this package pins
Python 3.12 and the tools want 3.13:

```bash
SK=$(readlink -f ~/.claude/skills/llm-claims-kb)/..
$SK/.venv/bin/llm.kb-validate docs/dev
$SK/.venv/bin/llm-claims-kb-mentions docs/dev/claims.kb
~/.claude/skills/llm-claims-kb/bin/llm-claims-kb-grounding docs/dev/claims.kb
~/.claude/skills/llm-claims-kb/bin/llm-claims-kb-graph docs/dev/claims.kb
```
