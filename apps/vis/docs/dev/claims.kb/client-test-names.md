---
label: CLIENT_TEST_NAMES
standing: agent
why:
- judge-on-own-authority.md
- ../../../../../.claude/todo.kb/2026-11-18-000-vis-app.kb/2026-11-18-006-client.md
---

# Client tests are named `{module}.test.ts`

Client tests sit beside their module as `{module}.test.ts`, the name
vitest finds with no configuration, against the house `{module}_test`
suffix. The house rule is written for Python
(`~/.claude/reference.kb/python/`), and the vitest name is what a
TypeScript reader expects. Unit 006 chose it, with that reason; the
coordinator adopted it.

Revisit if the house conventions gain a TypeScript rule that says
otherwise.
