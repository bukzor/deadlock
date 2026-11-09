# docs/dev

Developer docs: `llm-kb` knowledge bases, each a directory of per-topic files.
`ls` them to see the full range; read the one whose name matches before acting.

- `decisions.kb/` — why the project is built the way it is, one file per
  choice: tooling, build, data layout and test conventions. Read before
  changing an established approach.
- `formats.kb/` — reference for the on-disk formats we parse (VPK v2 container,
  Source 2 compiled `_c` resources, KV3) and the asset-type/extension inventory.
- `environment.kb/` — facts about this host and the game install that the code
  depends on (game-install paths, host Alpine/musl + gcompat quirks, the pinned
  toolchain).
- `mechanics.kb/` — how raw data fields combine into what a player sees (fire
  rate, DPS, cooldowns), each formula with its in-game evidence. Read before
  adding or changing a derived column.
- `game-runtime.kb/` — how the running game behaves (console, cvars, listen vs
  dedicated server, local bot-match hosting), dug out of binary strings and
  console logs. Read before driving or configuring the live game.
- `cvar-dump.kb/` — design of our own offline convar/concommand dumper (how
  the engine registers cvars, the capture approach and the options it beat,
  validation). Read before building or changing it.

`probes/` archives the one-off experiment scripts the KBs cite as evidence.

## Writing docs here

- State the current design and facts only. What changed and why belongs in
  commit messages; a devlog only when a commit message can't carry it.
- Cite only things that will keep existing. Never cite `trash/` or
  `scratchpad/`; archive a cited item into `probes/` instead.
