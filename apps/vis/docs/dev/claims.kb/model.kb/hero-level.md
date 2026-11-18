---
label: HERO_LEVEL
standing: user
authority:
  address: 14fac9c8#L1546
  words: inputs should include a "level" -- 0 is a good default, easieset to check in-game
  about: a level input on every timeline, and its default
---

# Every timeline takes the hero's level, default 0

The `timeline` query takes a `level`, and the client shows it for every
kind of ability, defaulting to 0, the level easiest to check in-game.
How a level changes the numbers is `LEVEL_SCALING`
([`level-scaling.md`](level-scaling.md)).

> [!@bukzor] 14fac9c8#L1546
> inputs should include a "level" -- 0 is a good default, easieset to check in-game
