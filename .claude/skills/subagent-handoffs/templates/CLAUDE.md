# Sub-agent handoffs for <the parent plan's goal>

Each file here is one sub-agent's unit of work toward the parent plan,
`../<plan>.md`. It carries both directions of the handoff: the coordinator's
brief, then the agent's own record and report. Belongs here: work one agent
can finish in one sitting (≤60 min), scoped to named files. Does not belong:
plan-level design (the parent plan), or work spanning waves (split it).

## Protocol

1. The coordinator writes the file before launch, named
   `YYYY-MM-DD-NNN-slug.md`: frontmatter `required-reading:` (this file, the
   upstream handoffs whose Final report it consumes) and `blocked-by:`; a
   **Problem Statement** (goal, scope as a file list, decisions already made
   for it). The launch prompt is only "do the task in <path>".
2. The agent works from the file and keeps it current: **Steps** as
   checkboxes (`[~]` / `[x]`), **Decisions** with reasons, **Open
   Questions**, and at the end a **Final report**: files touched, the exact
   public API it exposes (downstream briefs cite it), check results,
   deviations from the brief. `status:` stays `open` while it works (the
   schema has no in-progress value; `[~]` steps carry that). At the end it
   sets `status: done` and replies with the path only.
3. A later instruction is an in-place edit of the brief, and the message is
   just "reread <path>". The file always states the current truth, never a
   log of corrections: git carries its history, and the coordinator commits
   at each wave boundary.

## Every agent, every task

- Read first: <global and repo instructions, style/test conventions>, then
  the parent plan's sections named in the brief.
- Stay inside the brief's file list. Sibling agents run concurrently on
  other files; never edit theirs, the parent plan, or <shared docs>.
- Never stage, commit, or otherwise touch the git index.
- <Project rules: language/runtime limits, test layout, size limits.>
- Finish with <the project's checks> on the files you touched, clean.
- <Environment workarounds, added as agents discover them.>
- Scratch goes in <the repo's scratch dir>.
- The brief (frontmatter inputs, Problem Statement) is the coordinator's;
  edit only your own sections, in place, ≤60 lines.
