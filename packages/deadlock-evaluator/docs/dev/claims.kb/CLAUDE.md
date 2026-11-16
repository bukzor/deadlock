# claims.kb -- maintenance guide

The evaluator's design as a ledger; `../claims.md` is the entry point.

## What belongs here

A commitment the evaluator's design makes, a goal it answers to, a
representation or tool it chooses, or a question it has not yet closed.
Anything whose standing could be contested and whose reversal would
change what gets built.

## What does NOT belong here

How-to steps and conventions (those go in a CLAUDE.md or a procedure),
facts about game mechanics (`../../../../../docs/dev/mechanics.kb/` in the
`deadlock` package), and code. A file whose honest standing would be
`user` in every sibling is a manual, not a theory.

## Placing a claim

Pick the outermost theory that coins every coined word the text needs.
Words no theory coins are topic vocabulary and constrain nothing. When
two theories both want a word, read `Skill(llm-claims-kb)`'s confinement
audit before choosing.
