---
label: COMPILE
standing: agent
why:
- three-schemas-are-the-base.md
---

# compile is pure and emits breakpoints

`compile(Hero, Build, t) → StatVector` is a pure function of the
extracted game data: base stats, ability tiers, item modifiers,
stacking rules, caps, spirit scaling. Its nonlinearity is log-linear
and piecewise-linear only. Besides the vector it emits the breakpoints
(`../representation.kb/breakpoint-lattice.md`) and a provenance record
per stat (`../tooling.kb/provenance-records.md`). The `deadlock`
package's mechanics.kb is its seed.
