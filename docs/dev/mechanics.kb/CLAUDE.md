# mechanics.kb

How the game's numbers combine into gameplay: formulas that turn raw data
fields (``m_flCycleTime``, ``m_iBurstShotCount``, ...) into the quantities a
player sees (bullets per second, DPS, cooldowns).

What belongs: one mechanic per file — the formula, the raw fields it reads, and
the evidence for it. Ground truth is the in-game UI or observed behavior; record
the observations (hero, values, game build) beside the formula, and mark
anything not yet checked in-game as unverified.

What does not: where a field lives or how it is encoded (that's `../formats.kb/`),
how the running game/console/server behaves (that's `../game-runtime.kb/`), or why
a view is built the way it is (that's `../decisions.kb/`).

When to add: when a derived column in a `data/gamedata.tsv/` view depends on a
formula, or when the data disagrees with the obvious reading and in-game checks
settle it — before the knowledge exists only in a module docstring.
