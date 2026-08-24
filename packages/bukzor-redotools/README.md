# bukzor-redotools

Small companion commands for [apenwarr's redo](https://github.com/apenwarr/redo).

## `redo-adopt`

Marks existing files as redo-generated targets.

redo refuses to overwrite a file it didn't generate — djb's rule, so a
`default.c.do` can't clobber a hand-written `hello.c`. But it judges that from
its own state database, which a fresh `git clone` doesn't have. So a *committed*
build output looks hand-written, and redo skips it **while exiting 0**: the
build silently keeps stale content.

```sh
redo-adopt <path>...
```

After `redo-adopt PATH`:

- a target redo already owns and that nobody has touched is left alone — no
  rebuild is forced, so adopting repeatedly is free;
- in all other cases, including a `PATH` that doesn't exist yet, a subsequent
  redo will rebuild the target.

Adopting does *not* assert the file is up to date — with no dependency records
there would be no basis for that claim, and redo would then skip a stale file
forever.

Typical use — adopt the committed outputs at the top of your `all.do`, so a
fresh clone rebuilds them instead of trusting them:

```sh
redo-adopt "${committed[@]}"
```

## Caveat

There is no public API for this: upstream redo has no `redo-adopt`, and
`redo-stamp` only stamps the target of a running `.do` (used standalone it
leaves a half-initialized row that crashes the next build). So this imports
redo's own `state` module. That's a deliberately narrow dependency on internals
— three field assignments — and the test suite fails loudly if those semantics
ever shift. Developed against apenwarr redo 0.42d.
