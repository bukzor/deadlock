---
name: subagent-handoffs
description: Coordinate a multi-part implementation by delegating each small component to a sub-agent, with every handoff (brief and report) a reviewable file on disk. Load when the user asks to "use sub-agents" for a plan, to coordinate rather than implement, or when a plan's steps split into independent, file-scoped units.
---

# Sub-agent handoffs

The main session coordinates; sub-agents implement. The coordinator's context
is the scarce resource, so it writes briefs, reviews reports, and keeps the
plan current, but never does the components itself.

Every handoff, in both directions, is a file that can be reviewed, revised and
reused. A prompt or reply that exists only in chat is lost; back-filling it
later is too late, because the record should be what the agent actually worked
from.

## Layout

The units elaborate a parent plan, so they nest under it (`Skill(llm-kb)`,
"Where an Elaboration Goes"):

```
<plan>.md                  the plan; its step list links each handoff file
<plan>.jsonschema.yaml     handoff frontmatter schema (todo schema `$ref`)
<plan>.kb/
  CLAUDE.md                protocol + everything every agent shares
  YYYY-MM-DD-NNN-slug.md   one per unit: brief, then the agent's record
```

Claude Code loads a directory's `CLAUDE.md` when an agent reads a file in
it, so commonalities go there once instead of into every brief. Start it
from `templates/CLAUDE.md`, and start each brief from `templates/brief.md`.

## Procedure

1. **Decompose** the plan step into units: ≤60 min each, scoped to a disjoint
   file list. A file several units would touch (a manifest, a package
   `__init__`) belongs to exactly one of them.
2. **Order into waves** by API dependency. Units in a wave run in parallel;
   a wave starts when the reports it consumes are in. Record the waves in
   the plan as checkboxes, each linking its handoff file.
3. **Brief** each unit as a file before launch. Its frontmatter
   `required-reading:` names the `CLAUDE.md` and the upstream reports it
   builds on; refer to them instead of pasting. The launch prompt is
   one line: "Do the task in <path>; read its CLAUDE.md and
   required-reading first."
4. **Receive:** the agent replies with the path. Read its Final report,
   tick the plan's checkbox, and route what came back:
   - a rule or quirk every agent needs (an environment workaround) goes
     into `CLAUDE.md`;
   - a constraint on later units goes into those units' briefs;
   - a decision that belongs to the user goes to the user, briefly.
5. **Revise in place**, never re-brief in chat: edit the brief, then message
   "reread <path>". Files state the current truth; a mistake is deleted, not
   documented. History is git: commit at each wave boundary.

## Pitfalls

- The coordinator's own failure mode is "it's only two lines, I'll just fix
  it". Anything beyond reading reports, routing, and plan upkeep is a unit,
  including a tooling bug found along the way.
- Work owned by another repo gets its brief in that repo's `todo.kb/`,
  standalone: no `CLAUDE.md` covers it there, so inline the protocol.

- Never move or rename a handoff file while its agent is still running:
  `status: done` in the file comes before the agent's reply arrives.
- Sub-agents must not stage or commit; the coordinator owns git and the plan.
- In auto mode, a hook that rewrites Bash calls voids the review of any other
  call sent with it in the same response: write the brief (or amendment) in
  one response and launch or message in the next.
- A brief that names an API must say who owns it; when two parallel units
  need a shared type (an exception class), assign it to one and tell the
  other to wait or to stub it.
