# cvar-dump.kb

Design of a tool this project owns that dumps every cvar, convar and
concommand alike (name, flags, type, default, range, help), out of the game
DLLs, offline and deterministically. One file per design aspect: an engine
mechanism the design relies on, a choice it makes, or a check it runs.

What belongs: how the engine registers cvars, as far as the design depends on
it (cite SDK `file:line`, a binary string, or a run, plus the build); the capture
approach and the alternatives it beat; discovery, validation, and output shape.

What does not: what individual cvars do in the running game
(`../game-runtime.kb/`), host paths and quirks (`../environment.kb/`), project-wide
conventions (`../decisions.kb/`).

Tense: plain prose is fact (true of the engine, or true of built code).
`> [!TODO]` marks decided-but-unbuilt, `> [!QUESTION]` undecided — never
implement a `[!QUESTION]`. When a TODO lands, drop the callout so the sentence
stands as fact.

Prior art (read, not run): DumpSource2 at `00759ce`, s2sdk `deadlock` branch at
`18139bd`. Clone them fresh into the gitignored `trash/` when needed.
