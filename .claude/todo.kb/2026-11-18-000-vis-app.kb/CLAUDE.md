# Sub-agent handoffs for `apps/vis`

Each file in this directory is one sub-agent's unit of work toward the parent
plan, `../2026-11-18-000-vis-app.md`. It holds both directions of the handoff:
the coordinator's brief comes first, then the agent's own record and report.

- **Belongs here:** work one agent can finish in one sitting (≤60 min), scoped
  to named files.
- **Does not belong here:** design, which lives in
  `docs/dev/decisions.kb/vis-app.md`, and work that spans waves (split it).

A handoff file holds only what has no other home: what the unit was asked, how
far it got, what it chose, and what it still doubts. Design, interfaces and
findings live in their own homes. A handoff file links to them and never
copies them.

## Protocol

1. **Brief.** Before launch, the coordinator writes the file, named
   `YYYY-MM-DD-NNN-slug.md`. It has:
   - frontmatter `required-reading:` (this file, the design sections that
     govern the unit, and each interface the unit consumes, by path);
   - frontmatter `blocked-by:`;
   - a **Problem Statement**: the goal, the scope as a file list, and the
     decisions already made for the unit.

   The launch prompt is only "do the task in {path}".
2. **Work.** The agent works from the file and keeps it current:
   - **Steps** as checkboxes: `[~]` when a step starts, `[x]` when it ends;
   - **Decisions**, each with its reason;
   - **Open Questions**;
   - at the end, a **Final report**: check results, deviations from the brief,
     and where each result lives.

   `status:` stays `open` while the agent works. At the end the agent sets
   `status: done`, commits its unit, and replies with the path only.
3. **Amend.** While the file is open, a later instruction is an in-place edit
   of the brief, and the message is just "reread {path}". Once the file is
   done, it is a frozen record: nobody updates it, and a correction is a new
   unit.

## Every agent, every task

- **Read first:**
  - `~/.claude/CLAUDE.md`, and follow its `must-read.kb` procedure;
  - the repo's `CLAUDE.md`;
  - for Python, `~/.claude/reference.kb/python/{style,tdd}.md`;
  - then the brief's `required-reading:`.
- **Scope.** Stay inside the brief's file list. Sibling agents run concurrently
  on other files: never edit theirs, the parent plan or the design doc. If the
  design is wrong or silent, decide, and record the decision under Open
  Questions for the coordinator.
- **Interfaces.** Document an interface you produce where it is defined
  (docstrings, types), not in your report.
- **Commits.** Stage your scope's paths as you finish each step
  (`git -C /home/bukzor/claude/deadlock add {paths}`). Before handing back,
  commit them and your handoff file with `git commit-files {paths} -- -m
  {msg}`, per `~/.claude/must-read.kb/before/git/commit.md`.
  - Siblings share the index, so never commit bare, and never stage, unstage
    or commit a path outside your scope. On an `index.lock` collision, retry.
  - `docs/games/` is the user's untracked file: never stage it.
- **Server code** (`apps/vis/server/`):
  - Run things from that directory with `uv run pytest` and `uv run
    basedpyright`. The `VIRTUAL_ENV` mismatch warning is harmless.
  - Modules are ≤300 lines. Tests sit beside each module as `{module}_test.py`,
    named Describe/When/it.
  - Observe every assertion fail before trusting it. For a mutation run that
    rewrites a module in place, use `python -B` and delete that module's
    `__pycache__` entry, or a stale `.pyc` makes the mutant "survive".
    Restore the module afterwards.
  - Shared types go in `vis_server/types.py`. Nothing goes in `__init__.py`.
- **Real data** (local only, built by `redo` at the repo root):
  - `deadlock.gamedata.load` reads `data/gamedata.json/scripts/{heroes,abilities}.json`.
  - Hero display names are in `data/gamedata.tsv/heroes.tsv`.
  - Reuse `deadlock.*` (`abilities`, `ability_profiles`, `types`, `jsonl`,
    `paths`) before writing your own.
  - In `jq`, filter abilities with `.[]|objects`, because some top-level
    values are not objects.
- **Checks.** Finish with `pytest` and basedpyright `all` on the files you
  touched, both clean. The client's checks are `tsc --noEmit` and vitest.
- **Foreground only.** Run builds and checks in the foreground. Never end your
  turn waiting on a background job or a monitor. If a sibling must land first,
  say so in your report and stop; the coordinator resumes you.
- **Scratch** goes in `/home/bukzor/claude/deadlock/trash/` (gitignored), never
  `/tmp`.
- **Ownership.** The brief (frontmatter inputs, Problem Statement) belongs to
  the coordinator. Edit only your own sections, in place, in ≤60 lines.
- **Every save leaves the app working.** The user watches a live-reloading
  `bin/serve` (5173/8788) while you edit, and they want to keep it
  (`[!@bukzor]` 2026-11-18: "i mostly like the live view"). Only tests may go
  red in the middle of a change.
  - Change a signature in steps: add the new parameter with a default, update
    every caller, then drop the default.
  - Write a change that must span files at once in `trash/`, then move the
    files into place together.
  - Write new code first, and wire it into the app last.
- **`pnpm` is not on PATH.** It has been missing since about 16:50, and
  `volta` fails with a musl relocation error. The client's own tools work from
  `apps/vis/client/node_modules/.bin/`. Don't repair the user's global setup.
  Report what you used instead.
