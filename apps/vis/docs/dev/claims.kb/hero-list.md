---
label: HERO_LIST
standing: agent
why:
- judge-on-own-authority.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-020-ux-review-2.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-023-player-words-server.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-025-hero-filter.md
---

# The hero list leaves out disabled heroes, which still answer by key

`heroes` lists live heroes by display name, leaving out every hero whose
`heroes.tsv` row is `disabled` or has no name, plus `hero_genericperson` and
`hero_targetdummy`. It filters on `disabled`, not `in_development`: Violet
and Baba are `in_development` yet bound and pickable, and Kali is `disabled`
yet not `in_development`. (Unit 023 filtered on `in_development` and
dropped Violet and Baba; unit 025 corrected it.) `abilities` and `timeline`
still answer for a left-out hero by key, so a shared URL naming one keeps
working. Declined: rejecting them there too, which breaks such URLs for no
gain. Overturned if the owner wants a disabled hero, Kali especially,
listed. Built in `apps/vis/server/src/vis_server/queries.py` (`listed`).
