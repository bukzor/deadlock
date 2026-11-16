---
label: WPA
standing: agent
why:
- macro-state-path.md
- ../goals.kb/one-currency-for-all-decisions.md
---

# Win probability added is the common currency

Fit a value function V on the macro-state path. The value of any
episode or decision is the change in V across it. Skill points, items,
fights and rotations are then valued in one unit, and credit
assignment is additive across a match. Sports analytics has run this
shape for decades (expected points added, win probability added), and
it is robust because the state it is fit on is tiny. Fitting V comes
after the first loop closes (`../architecture.kb/build-order-of-work.md`).
