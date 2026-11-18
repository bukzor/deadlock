# apps/vis/docs/dev

The ledger of `apps/vis`'s judgement calls, `claims.md` beside
`claims.kb/`, kept per `Skill(llm-claims-kb)`. Read `claims.md` first.
The design itself is `docs/dev/decisions.kb/vis-app.md` at the repo
root; a claim here links to it and never restates it.

## Telling settled from suggested

`standing:` is the whole answer to "is this decided?": `user` is the
owner's ruling, quoted with its address; `agent` is a call in force,
veto invited, never cite one as the owner's; `open` is a question;
`bare` is a checked fact. A struck claim keeps its file and gains
`verdict:`. The owner's words appear only as `> [!@bukzor] <address>`
callouts quoted from the session log.

## Where a new file goes

A call inside the damage model, which an in-game measurement could
overturn, goes in `claims.kb/model.kb/`; any other call goes in
`claims.kb/`. A new owner ruling goes in `claims.kb/` as a `user` claim.
Run the ledger tools from the skills workspace's venv:

```bash
SK=$(readlink -f ~/.claude/skills/llm-claims-kb)/..
$SK/.venv/bin/llm.kb-validate apps/vis/docs/dev
$SK/.venv/bin/llm-claims-kb-mentions apps/vis/docs/dev/claims.kb
~/.claude/skills/llm-claims-kb/bin/llm-claims-kb-grounding apps/vis/docs/dev/claims.kb
~/.claude/skills/llm-claims-kb/bin/llm-claims-kb-graph apps/vis/docs/dev/claims.kb
```
