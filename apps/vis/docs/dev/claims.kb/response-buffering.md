---
label: RESPONSE_BUFFERING
standing: agent
why:
- judge-on-own-authority.md
- ../../../../../docs/dev/decisions.kb/vis-app.md
---

# A JSONL response is built whole, then sent

The server builds a query's whole response before sending its first
byte, so a `BadRequest` raised partway through still becomes a 400 with
one `{"error": ...}` line. Declined: streaming lines as they are made,
which commits a 200 before the error is known and leaves the client a
truncated body to tell apart from a short answer.

This is the simple option `OWN_AUTHORITY` allows. Streaming can come
later by changing the server alone, because the client already parses
line by line (`apps/vis/client/src/jsonl.ts`). Revisit when a query's
output is large enough to wait on, or a view needs server push. Design:
[`vis-app.md`](../../../../../docs/dev/decisions.kb/vis-app.md),
*Protocol* and *What would change this*. Built by unit 009.
