# environment.kb

Facts about this host and the Deadlock install that the code and tooling depend
on: filesystem paths, OS/libc quirks, and pinned versions of external tools and
the game itself.

What belongs: things that are true of *this machine* (or the current install)
and would surprise an agent assuming a stock Linux box — paths under
`/mnt/c`, the musl/gcompat situation, the pinned VRF version, how the box boots.

What does not: format details (`formats.kb/`), rationale for choices
(`decisions.kb/`). State the fact and where it's configured; put the "why we
chose X" in a decision.

When to add/update: when a path, version, or host assumption changes, or when you
discover a host quirk that cost you time. Keep version pins here in sync with what
the code/scripts actually use.
