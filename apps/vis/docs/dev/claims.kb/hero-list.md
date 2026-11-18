---
label: HERO_LIST
standing: agent
why:
- judge-on-own-authority.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-023-player-words-server.md
---

# The hero list leaves out in-development heroes, which still answer by key

`heroes` lists live heroes by display name, leaving out every hero whose
`heroes.tsv` row has `in_development` true, and `hero_targetdummy`. On the
build of 2026-11-11 that leaves 42, and drops Violet among others, whose
row is `in_development` though she is bound and appeared in the picker.
`abilities` and `timeline` still answer for a left-out hero by key, so a
shared URL naming one keeps working. Declined: rejecting them there too,
which breaks such URLs for no gain. Overturned if the owner wants a
left-out hero, Violet especially, back in the list. Built in
`apps/vis/server/src/vis_server/queries.py` (`listed`).
