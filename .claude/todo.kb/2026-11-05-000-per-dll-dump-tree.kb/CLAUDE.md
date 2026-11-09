# Sub-agent handoffs for the per-DLL store

Each file here is one sub-agent's unit of work toward the parent plan,
`../2026-11-05-000-per-dll-dump-tree.md`. It carries both directions of the
handoff: the coordinator's brief, then the agent's own record and report. Belongs
here: work one agent can finish in one sitting (≤60 min), scoped to named
files. Does not belong: plan-level design (the parent plan, or
`docs/dev/convar-dump.kb/`), or work spanning waves (split it).

## Protocol

1. The coordinator writes the file before launch, named
   `YYYY-MM-DD-NNN-slug.md`: frontmatter `required-reading:` (this file,
   the upstream handoffs whose Final report it consumes) and `blocked-by:`;
   a **Problem Statement** (goal, scope as a file list, decisions already
   made for it). The launch prompt is only "do the task in <path>".
2. The agent works from the file and keeps it current: **Steps** as
   checkboxes (`[~]` / `[x]`), **Decisions** with reasons, **Open
   Questions**, and at the end a **Final report**: files touched, the exact
   public API it exposes (downstream briefs quote it), check results,
   deviations from the brief. `status:` stays `open` while it works (the
   schema has no in-progress value; `[~]` steps carry that). At the end it
   sets `status: done` and replies with the path only.
3. A later instruction is an in-place edit of the brief, and the message is
   just "reread <path>". The file always states the current truth, never a
   log of corrections: git carries its history, and the coordinator commits
   at each wave boundary.

## Every agent, every task

- Read first: `~/.claude/CLAUDE.md` and its `must-read.kb` procedure, the
  repo's `CLAUDE.md`, `~/.claude/reference.kb/python/{style,tdd}.md`, then
  the parent plan's sections named in the brief.
- Facet documents are JSON whose types fit the data; views adapt them to
  their format (`docs/dev/convar-dump.kb/output-views.md`, JSON content rules).
- Stay inside the brief's file list. Sibling agents run concurrently on
  other files; never edit theirs, the parent plan, or `docs/`.
- Never stage, commit, or otherwise touch the git index: the tree carries
  unrelated uncommitted work.
- `src/dllscan/`: stdlib only (`stdlib_only_test.py` enforces it, test files
  exempt), 3.12-compatible, modules ≤300 lines, tests beside as
  `*_test.py`, Describe/it. Observe every assertion fail before trusting it.
- Finish with `pytest` and `pyright` on the files you touched, clean. If
  the repo's `bin/shell` reports "command not found", inherited direnv state is
  hiding `.venv/bin`: prefix
  `env -u DIRENV_DIR -u DIRENV_DIFF -u DIRENV_WATCHES -u DIRENV_FILE`.
- Scratch goes in the repo's `trash/` (gitignored), never `/tmp`.
- Mutation runs that rewrite a module in place: run with `python -B` and
  delete that module's `__pycache__` entry, or a mutant written within the
  same second, at the same size, imports the stale `.pyc` and "survives".
- The brief (frontmatter inputs, Problem Statement) is the coordinator's;
  edit only your own sections, in place, ≤60 lines.
