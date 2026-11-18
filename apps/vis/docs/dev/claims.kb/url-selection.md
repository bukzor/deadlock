---
label: URL_SELECTION
standing: agent
why:
- original-request.md
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# The selection lives in the URL now; comparison overlays wait

The hero, ability and parameters live in the URL, so a page reloads and
shares. Declined for now: overlaying a second selection's cumulative line to
compare two sources, and patch-versus-patch views, which finding 6 sizes at M
and L. They go beyond the request's first goal. Revisit when the owner wants
comparisons. Built by unit 017.

The owner asked for the review that produced this call ("a sub-agent to
ponder the intelligibility and overall UX of this UI", quoted in unit 015's
brief); the finding is in
unit 015's report (`git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md`). Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md).

Provenance (the handoff files are retired): `git show b3e9e17:.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-015-ux-review.md`.
