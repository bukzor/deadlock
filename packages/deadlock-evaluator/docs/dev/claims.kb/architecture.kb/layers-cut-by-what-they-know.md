---
label: LAYERS
standing: agent
why:
- ../goals.kb/base-before-branches.md
---

# Layers are cut by what each knows

| Layer | Knows about | Components |
|---|---|---|
| L0 extraction | binary and VPK formats | the `deadlock` package |
| L1 static semantics | game rules, no dynamics | compile, economy |
| L2 dynamics | how a fight unfolds | engage |
| L3 empirics | the real world | observe, measure |
| L4 generic operators | nothing about the game | compare, aggregate, attribute, search, pareto |
| L5 applications | the goals | compositions |

Cutting by knowledge rather than by data flow is what keeps a layer
swappable: L2 can be replaced without L4 noticing. The alternative,
one pipeline per goal, was declined by the owner's base-first ruling.
