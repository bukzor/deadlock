# Ask the running game: `cvarlist` (declined as source; kept as oracle)

`tier0.dll` registers `cvarlist`, `find`, `help`, `findflags`, `differences`;
its listing columns are name, value, default, bounds, flags, help text (strings
near `cvarlist` in `tier0.dll`, 6848). Run e.g.
`deadlock.exe -dedicated +cvarlist +quit -condebug` and parse the log.

For: zero reverse engineering — the engine's own answer.

Against: retail hides `developmentonly` (`citadel_bot_kick` is "unknown
command" in-game, `../../game-runtime.kb/local-bot-match-lobby.md`), ~3000 of
them; a dedicated server lacks client cvars, so a full client launch is needed
too; launches the game.

Its independence is exactly what the dumper lacks, so it is the cross-check in
`../validation.md`.

> [!QUESTION] Unverified that `cvarlist` omits `developmentonly` entries; and the
> exact flag spelling it prints.
