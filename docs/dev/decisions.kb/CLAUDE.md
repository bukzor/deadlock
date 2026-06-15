# decisions.kb

One file per architectural or tooling decision that shapes the project, with the
rationale a future maintainer needs to evaluate or revisit it.

What belongs: choices with non-obvious tradeoffs that we'd otherwise re-litigate
— which external tool to depend on, how outputs are produced, project-wide
conventions. Capture *why*, the alternatives weighed, and what would change the
decision.

What does not: transient task notes, how-to steps (those are procedures), and
descriptions of file formats or the host (those are `formats.kb/` and
`environment.kb/`).

When to add: when you make a call that a later agent might unknowingly reverse.
When superseding one, set the old file's `status: superseded` and the new file's
`supersedes:` to the old filename rather than deleting history.

Frontmatter is required and validated by `../decisions.jsonschema.yaml`.
