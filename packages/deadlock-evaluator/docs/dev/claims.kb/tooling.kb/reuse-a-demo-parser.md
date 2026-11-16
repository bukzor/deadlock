---
label: DEMO_PARSER_REUSE
standing: agent
why:
- ../architecture.kb/observe-parses-replays.md
---

# Reuse an existing Deadlock demo parser

Source 2 demo parsers for Deadlock exist in Rust. observe wraps one
and has it emit Parquet or JSON lines into the store, in keeping with
the parent project's reuse-before-inventing decision. Which parser,
and whether it exposes positions, is unverified.
