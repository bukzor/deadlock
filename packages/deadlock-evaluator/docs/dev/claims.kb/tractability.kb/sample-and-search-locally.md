---
label: SAMPLE_LOCAL
standing: agent
why:
- one-principle-not-one-algorithm.md
- ../architecture.kb/observe-parses-replays.md
---

# Sample instead of enumerate; search near observed builds

Never enumerate situations: the replay corpus is a sample from the
real distribution. Never search build space globally: public builds
are the output of a search millions of players already ran, so start
there and hill-climb or beam-search their neighborhoods. Shapley by
sampled permutations. The whole of "auto-create builds" is thereby
"locally improve observed builds".
