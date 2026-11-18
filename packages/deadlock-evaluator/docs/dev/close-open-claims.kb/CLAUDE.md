# Sub-agent handoffs for closing the evaluator ledger's open claims

Each file here is one sub-agent's unit of work toward the parent plan,
`../close-open-claims.md`. It carries both directions of the handoff: the
coordinator's brief, then the agent's own record and report. Belongs here:
work one agent can finish in one sitting (≤60 min), scoped to named files.
Does not belong: design (`../claims.md` and `../claims.kb/`), or work
spanning waves (split it).

A handoff file holds only what has no other home: what the unit was asked,
how far it got, what it chose and still doubts. Design, interfaces and
findings live in their own homes, and a handoff file links to them, never
copies them.

## Protocol

1. The coordinator writes the file before launch, named
   `YYYY-MM-DD-NNN-slug.md`: frontmatter `required-reading:` (this file, the
   doc sections that govern the unit, the interfaces it consumes by path)
   and `blocked-by:`; a **Problem Statement** (goal, scope as a file list,
   decisions already made for it). The launch prompt is only "do the task in
   {{path}}".
2. The agent works from the file and keeps it current: **Steps** as
   checkboxes, marked `[~]` on starting one and `[x]` on finishing it, so an
   interrupted unit can resume where it stopped; **Decisions** with reasons;
   **Open Questions**. At the end, a **Final report**: check results,
   deviations from the brief, and where each result lives (the paths that
   define an interface, the doc a finding went into). `status:` stays
   `open` while it works; at the end it sets `status: done`, commits its
   unit, and replies with the path only.
3. While open, a later instruction is an in-place edit of the brief, and the
   message is just "reread {{path}}". Once done, the file is a frozen record:
   nobody updates it, and a correction is a new unit.

## Every agent, every task

- Read first: `~/.claude/CLAUDE.md`, the repo's `CLAUDE.md` (two levels up
  from `packages/`), `../CLAUDE.md` (this package's docs guide), then the
  brief's `required-reading:`.
- Stay inside the brief's file list. Sibling agents run concurrently on
  other files; never edit theirs or the parent plan.
- Write each finding into its home, the doc your scope names. When there is
  none, the Final report is its home; name the gap in Open Questions.
- A finding that lands in a claim file follows `Skill(llm-claims-kb)`'s
  mapping: a measured number makes the claim `standing: bare` with a
  `verify:` command that reproduces it; your own judgment stays
  `standing: agent`; never write in the owner's voice. Keep the body under
  120 words. Validate with the commands in `../CLAUDE.md`.
- An interface you produce is documented where it is defined (docstrings,
  types, a `.do` recipe's header comment), not restated in your report.
- Stage your scope's paths as you finish each step (`git add PATHS`).
  Before handing back, commit them and your handoff file with
  `git -C <repo> commit-files PATHS -- -m MSG` (see
  `~/.claude/reference.kb/git/commit.md`). Siblings share the index: never
  commit bare, and never stage, unstage or commit a path outside your
  scope. On an `index.lock` collision, retry.
- Project rules: run everything through `./bin/shell <cmd>` from the repo
  root; Python via `uv`, modules ≤300 lines; bash ≤50 lines; vendored
  tools are redo targets under `data/tools/` (pattern:
  `data/tools/Source2Viewer-CLI.d.do`) and are gitignored except their
  `.do` files; nothing under `data/` is committed except `.do` files.
- The game install is at `/mnt/c/Program Files (x86)/Steam/steamapps/common/Deadlock`
  (`docs/dev/environment.kb/game-install-paths.md` at the repo root). Seven
  local bot-match recordings sit at `game/citadel/botmatch*.dem` under it,
  74 to 92 MB each. Read them in place; never write there.
- Downloaded archives and demos are untrusted data: each in its own empty
  directory, scripts elsewhere, Python that reads them run with `-I`.
- Run builds and checks in the foreground. Never end your turn waiting on a
  background job: if a sibling must land first, say so in your report and
  stop; the coordinator resumes you.
- Scratch goes in the repo root's `trash/<unit-NNN>/`; it is gitignored.
- The brief (frontmatter inputs, Problem Statement) is the coordinator's;
  edit only your own sections, in place, ≤60 lines.
- Timebox: 60 minutes. Past it, write the Final report with what you have
  and what blocked you, and stop.
