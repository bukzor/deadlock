# Sub-agent handoffs for the package split

Each file here is one sub-agent's unit of work toward the parent plan,
`../2026-11-23-000-package-split.md`. It carries both directions of the
handoff: the coordinator's brief, then the agent's own record and report.
Belongs here: work one agent can finish in one sitting (≤60 min), scoped to
named files. Does not belong: design (the target layout and its reasons are
`docs/dev/decisions.kb/small-bukzor-prefixed-packages.md`), or work spanning
waves (split it).

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
  types), not restated in your report.
- **Moves stay moves.** Use `git mv`, and keep a moved file's content edits
  to what the move forces (imports, paths, names), so git still pairs the
  rename. Commit the rename pair: both the old and the new path
  (`~/.claude/reference.kb/git/commit.md`, "Rename pairs").
- **Frozen records are never edited:** a `status: done` handoff file in any
  `*.kb/` (`.claude/todo.kb/*.kb/`, the evaluator's
  `docs/dev/close-open-claims.kb/`), and anything under `trash/`. They may
  move with their directory; their text keeps the old names.
- The game is "Deadlock"; only the *package* names change. Leave the game's
  name, the repo directory and `data/` paths alone.
- Stage your scope's paths as you finish each step. Before handing back,
  commit them and your handoff file with
  `git -C <repo> commit-files PATHS -- -m MSG` (see
  `~/.claude/reference.kb/git/commit.md`). Siblings share the index: never
  commit bare, and never stage, unstage or commit a path outside your scope.
  On an `index.lock` collision, retry.
- **Never `git stash`**, nor any other command that rewrites the whole
  index or worktree (`git reset` without paths, `git checkout .`): siblings'
  staged and unstaged work lives there. To look at `HEAD`, use `git show
  HEAD:PATH` or a scratch `git worktree add` under `trash/<unit-NNN>/`.
- Project rules: run root tooling through `./bin/shell <cmd>`; vis tooling
  with `uv run <cmd>` from `apps/vis/server`. Python modules ≤300 lines.
  Never hand-edit a `uv.lock`: `uv lock` / `uv sync` rewrite it. New files
  are `black`-clean (`./bin/shell black FILE`); never reformat a file you
  only move or lightly edit (a repo-wide black pass is its own todo).
- Finish with all of these clean, on top of your brief's own checks:
  - root: `./bin/shell pytest` and `./bin/shell pyright`
  - vis: `uv run pytest` and `uv run basedpyright` in `apps/vis/server`
  - the vis protocol byte for byte: from `apps/vis/server`,
    `uv run python ../../../.claude/todo.kb/2026-11-23-000-package-split.kb/golden.py > ../../../trash/<unit-NNN>/golden.after.txt`,
    then `cmp` it against `trash/package-split/golden.before.txt` (captured
    before wave 1; never overwrite it)
- Sync the root venv with `uv sync --all-packages`; a plain `uv sync`
  prunes workspace members' dependencies (the evaluator's `boon-deadlock`,
  `polars`). Wave-2 units touch no dependency list, so they rarely need it.
- A check that was red before your unit (try it on `HEAD` in a scratch
  worktree) is not yours to fix: report it.
- Run builds and checks in the foreground. Never end your turn waiting on a
  background job: if a sibling must land first, say so in your report and
  stop; the coordinator resumes you.
- Scratch goes in the repo root's `trash/<unit-NNN>/` (gitignored).
- The brief (frontmatter inputs, Problem Statement) is the coordinator's;
  edit only your own sections, in place, ≤60 lines.
- Timebox: 60 minutes. Past it, write the Final report with what you have
  and what blocked you, and stop.
