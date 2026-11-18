# Close the ledger's open claims

The design ledger (`claims.md`) held four `standing: open` claims, then a
fifth filed by the owner mid-plan. Three are empirical and are closed by
measurement; two are rulings only the owner can make. This plan runs the measurements as sub-agent units
(`Skill(subagent-handoffs)`), one handoff file per unit in
`close-open-claims.kb/`.

| Open claim | File | Closed by |
|---|---|---|
| `EVENT_VOLUME` | `claims.kb/tooling.kb/event-volume-per-demo.md` | units 001, 002, 003 |
| `SEGMENTATION` | `claims.kb/representation.kb/segmentation-from-events.md` | unit 004 |
| `OUTCOME_TRACE` | `claims.kb/architecture.kb/outcome-trace-or-summary.md` | owner's ruling, not a unit |
| `MICRO_POLICY` | `claims.kb/architecture.kb/micro-policy-is-the-open-input.md` | owner narrows it now; calibration closes it later |
| `LOCAL_DEMO_TRIGGERS` | `claims.kb/tooling.kb/local-demo-corpus-triggers.md` | unit 005 from disk evidence; one owner observation if it stays open |

Also settled along the way, though never filed as open: which demo parser
`observe` wraps and whether it exposes positions
(`claims.kb/tooling.kb/reuse-a-demo-parser.md`), and whether a bot-match
demo differs materially from a public match.

## Waves

Wave 1 (parallel):
- [x] [001 demo parser](close-open-claims.kb/2026-11-18-001-demo-parser.md): pick and vendor a Deadlock demo parser, prove it on a local bot-match demo
- [x] [003 public demo](close-open-claims.kb/2026-11-18-003-public-demo.md): obtain one real public match demo

Wave 2:
- [x] [002 event volume](close-open-claims.kb/2026-11-18-002-event-volume.md): count rows by event type on a bot and a public demo; close `EVENT_VOLUME`

Wave 3:
- [x] [004 segmentation](close-open-claims.kb/2026-11-18-004-segmentation.md): cut one demo into episodes from damage events; close `SEGMENTATION`

Wave 4:
- [ ] [005 demo triggers](close-open-claims.kb/2026-11-18-005-demo-triggers.md): what writes each kind of file under the install's `replays/`; close or narrow `LOCAL_DEMO_TRIGGERS`

## Success criteria

- `EVENT_VOLUME` and `SEGMENTATION` carry `standing: bare` with a `verify:`
  command that reruns the measurement, or stay `open` with the reason filed.
- `reuse-a-demo-parser.md` names the parser and what it exposes.
- `grep -rl 'standing: open' claims.kb/` lists only owner-ruling claims.

Commit range: 2041c59..HEAD (plan, four units, routing). Review pending;
the handoff files are removed once the owner is satisfied.
