# game-runtime.kb

How the running game behaves — client, listen server, dedicated server, console
and cvars — as learned from the binaries' strings and the console logs, not from
play folklore. One topic per file.

What belongs: durable facts about runtime behavior worth not re-deriving (who
may change a cvar, which cfg the server execs and when, how a local match is
hosted). Cite the evidence (binary + string, or log + line/timestamp) and the
build it was observed on; mark inference as such — these change with patches.

What does not: on-disk formats (`formats.kb/`), install paths and host quirks
(`environment.kb/`), why the project is built a certain way (`decisions.kb/`).

When to add: when you dig a runtime behavior out of the binaries or logs, or
when a patch invalidates a fact here (fix it, bumping the build).
