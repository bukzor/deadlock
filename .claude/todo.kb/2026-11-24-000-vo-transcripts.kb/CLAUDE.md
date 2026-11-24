# Sub-agent handoffs for VO transcripts

Each file here is one sub-agent's unit of work toward the parent plan,
`../2026-11-24-000-vo-transcripts.md`. It carries both directions of the
handoff: the coordinator's brief, then the agent's own record and report.
Belongs here: work one agent can finish in one sitting (≤60 min), scoped to
named files. Does not belong: design (`docs/dev/`), or work spanning waves
(split it).

A handoff file holds only what has no other home: what the unit was asked,
how far it got, what it chose and still doubts. Design, interfaces and
findings live in their own homes, and a handoff file links to them, never
copies them.

## Protocol

1. The coordinator writes the file before launch, named
   `YYYY-MM-DD-NNN-slug.md`: frontmatter `required-reading:` and
   `blocked-by:`; a **Problem Statement** (goal, scope as a file list,
   decisions already made for it). The launch prompt is only "do the task in
   {path}".
2. The agent works from the file and keeps it current: **Steps** as
   checkboxes, marked `[~]` on starting one and `[x]` on finishing it, so an
   interrupted unit can resume where it stopped; **Decisions** with reasons;
   **Open Questions**. At the end, a **Final report**: check results,
   deviations from the brief, and where each result lives. `status:` stays
   `open` while it works; at the end it sets `status: done`, commits its
   unit, and replies with the path only.
3. While open, a later instruction is an in-place edit of the brief, and the
   message is just "reread {path}". Once done, the file is a frozen record:
   nobody updates it, and a correction is a new unit.

## Every agent, every task

- Read first: `~/.claude/CLAUDE.md` (and the must-read triggers it
  installs), the repo's `CLAUDE.md`, `docs/dev/CLAUDE.md`, then the brief's
  `required-reading:`.
- Stay inside the brief's file list. A sibling may run concurrently on other
  files; never edit theirs or the parent plan.
- Write each finding into its home, the doc your scope names. When there is
  none, the Final report is its home; name the gap in Open Questions.
- An interface you produce is documented where it is defined (docstrings,
  types, the `.do` header), not restated in your report.
- **Disk:** `/` is a growable virtual disk stored on C:
  (`.../AlpineWSL_.../LocalState/ext4.vhdx`), so `df /` overstates the
  space. The real limit is `df /mnt/c`. Running C: out of space crashes
  the whole session, which happened on 2026-11-24 with 26 GB of explode.
  Deleting files doesn't shrink the vhdx. Before any write over about
  1 GB, estimate its size (for a VPK, sum the index's entry sizes) and keep
  at least 20 GB free on C:.
- **CPU, from 2026-11-24 on:** the owner works in the foreground. Run every
  CPU-heavy job (whisper, bulk ffmpeg) under `nice -n 19`, with at most 4
  threads across all your concurrent jobs. That is the whole budget, not
  per process.
- Read the install in place; never write under `$DEADLOCK_HOME`. It is a
  Windows drive seen through WSL (9P), so reads are slow: measure before you
  bulk-copy.
- Stage your scope's paths as you finish each step. Before handing back,
  commit them and your handoff file with
  `git -C <repo> commit-files PATHS -- -m MSG` (see
  `~/.claude/reference.kb/git/commit.md`). Siblings share the index: never
  commit bare, and never stage, unstage or commit a path outside your scope.
  On an `index.lock` collision, retry. `docs/dev/mechanics.kb/` holds the
  owner's uncommitted work: never touch it.
- **Never `git stash`**, nor any other command that rewrites the whole
  index or worktree.
- Project rules: run tooling through `./bin/shell <cmd>`. Python modules
  ≤300 lines, tests beside them as `{module}_test.py`. Never hand-edit
  `uv.lock`; use `uv add`. New files are `black`-clean.
- Finish with `./bin/shell pytest` and `./bin/shell pyright` clean. A check
  that was red before your unit is not yours to fix: report it.
- Run builds and checks in the foreground. Never end your turn waiting on a
  background job: if a sibling must land first, say so in your report and
  stop; the coordinator resumes you.
- Scratch goes in the repo root's `trash/vo-transcripts/<NNN>/` (gitignored;
  bare `trash/<NNN>/` belongs to an earlier plan).
- The brief (frontmatter inputs, Problem Statement) is the coordinator's;
  edit only your own sections, in place, ≤60 lines.
- Timebox: 60 minutes. Past it, write the Final report with what you have
  and what blocked you, and stop.
