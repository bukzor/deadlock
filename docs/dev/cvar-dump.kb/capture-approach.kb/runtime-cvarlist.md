# Ask the running game: `cvarlist` (declined as source; kept as oracle)

`tier0.dll` registers `cvarlist`, `find`, `help`, `findflags`, `differences`.
Its listing columns are name, current value, flags, help. Defaults and
bounds print only via `help <name>`. Capture both sides with
`bin/cvarlist-capture` and parse the log. Format, flag spelling and coverage:
`../../game-runtime.kb/cvarlist-capture.md`.

For: zero reverse engineering — the engine's own answer.

Against: the listing omits `developmentonly` and `hidden` declarations and
the `-` half of `+`/`-` commands (6860: 4629 of the store's 7641 rows are
`developmentonly`); it prints current values, which `gameinfo.gi` and the
user's settings move off the declared defaults; a dedicated server lacks
client cvars, so a full client launch is needed too; launches the game.

Its independence is exactly what the dumper lacks, so it is the cross-check in
`../validation.md`.
