# Sub-agent handoffs for item names

Each file here is one sub-agent's unit of work toward the parent plan,
`../2026-11-25-000-item-names.md`. It carries both directions of the handoff:
the coordinator's brief, then the agent's own record and report. Belongs
here: work one agent can finish in one sitting (≤60 min), scoped to named
files. Does not belong: design (`docs/dev/`), or work spanning waves (split
it).

A handoff file holds only what has no other home: what the unit was asked,
how far it got, what it chose and still doubts. Design, interfaces and
findings live in their own homes, and a handoff file links to them, never
copies them.

## Protocol

1. The coordinator writes the file before launch: frontmatter
   `required-reading:` and `blocked-by:`, then a **Problem Statement** (the
   goal, the scope as a file list, decisions already made). The launch
   prompt is only "do the task in {path}".
2. The agent works from the file and keeps it current: **Steps** as
   checkboxes (`[~]` when started, `[x]` when finished), **Decisions** with
   reasons, **Open Questions**. At the end it writes a **Final report**:
   check results, deviations from the brief, and where each result lives.
   Then it sets `status: done`, commits its unit, and replies with the path
   only.
3. While the file is open, a later instruction is an in-place edit, and the
   message is "reread {path}". Once it is done, the file is frozen.

## Every agent, every task

- Read first: `~/.claude/CLAUDE.md` (and the must-read triggers it
  installs), the repo's `CLAUDE.md`, `docs/dev/CLAUDE.md`, then the brief's
  `required-reading:`.
- Stay inside the brief's file list.
- Read the install in place; never write under `$DEADLOCK_HOME`.
- Stage your scope's paths as you go. Before handing back, commit them and
  your handoff file with `git -C <repo> commit-files PATHS -- -m MSG` (see
  `~/.claude/reference.kb/git/commit.md`). Never commit bare, and never
  stage or commit a path outside your scope. `docs/dev/mechanics.kb/`,
  `docs/games/` and `listen.sh` hold the owner's uncommitted work: never
  touch them. **Never `git stash`.**
- Project rules: run tooling through `./bin/shell <cmd>`. Python modules
  ≤300 lines, tests beside them as `{module}_test.py`. New code is
  `black`-clean.
- Finish with `./bin/shell pytest` and `./bin/shell pyright` clean. A check
  that was red before your unit is not yours to fix: report it.
- Scratch goes in the repo root's `trash/item-names/<NNN>/`.
- The brief (frontmatter, Problem Statement) is the coordinator's. Edit only
  your own sections, in place, ≤60 lines.
