# Output: a lossless store of data about the DLLs; views derived from it

Per `../decisions.kb/commit-diffable-data-let-git-diff.md`, shaped like the
existing `gamedata` pipeline (`gamedata.list` → `gamedata.json/` →
`gamedata.tsv/`). Convars and concommands are the first purpose, not the
store's shape. A **facet** is one side of a DLL that one producer dumps (its
file, its load, its convar queue); each facet is dumped losslessly for every
DLL, and a purpose is a filter or view over the store, so the store stays
valid for the next question about DLLs.

The layout is facet-first under one root, one process per (facet, DLL)
(`../decisions.kb/lossless-per-dll-store-with-atomic-facets.md`):

- `data/dlls.list` (gitignored, like `gamedata.list`): membership only, every
  `*.dll` under `game/`, one path per line relative to `game/`. DLL basenames
  are unique (97 DLLs, 6860), so a basename keys everything below. Nothing
  that changes on a patch goes here: every atom depends on this file, so a
  size or hash in it would re-run them all. It is rebuilt when the build stamp
  changes, not on every build.
- `data/dlls/<facet>/default.json.do` (the documents gitignored: near-verbatim
  Valve data): one facet of one DLL → one JSON document; `$2` is the basename.
  Guard: the name must be in `dlls.list`, and for a load-time facet
  `load/<dll>.json` must say `ok`; anything else fails loudly. No atom reads
  another DLL's document, so atoms are independent and `redo -j` runs them in
  parallel. Process overhead is ~0.2 s per atom (6860,
  `../probes/load_time.py`).
- `data/dlls/default.tsv.do`: a case table on the facet, as
  `gamedata.dense.tsv/default.tsv.do` has. Each calls `redo-ifchange` once
  over its facet's documents (one call, so redo parallelises): every DLL in
  `dlls.list` for `file` and `load`, every `ok` one for a load-time facet. Then
  a WSL-side `deadlock.dlls_<facet>` module writes `<facet>.tsv`, the facet's
  lossless aggregate. All four are committed.

The facets: `file` (size, sha256), `load` (outcome: `ok` with the modules the
load pulled in, `failed` with the error, or `excluded` with its reason;
`dll-coverage.md`), `convars`, `concommands`.

> [!TODO] Later facets: `pe` (static PE metadata; relocations and `.pdata` as
> count + hash, the rest whole: 14 MB for all 97 in `pefile`'s own shape,
> 6860, `../probes/pe_size.py`), `interfaces` (the `InterfaceReg` list),
> logging channels, schemas.

A `convars` or `concommands` document is the lossless record of one queue: a
list in queue order, every declaration kept, duplicates included: on 6854
`server.dll` alone declares `developer` and three `citadel_*_reveal_duration`
more than once (2008 declarations, 2003 names). Commands are their own facet,
not convars: separate creation struct, queue, registration slot and registry
(`registration-flow.md`). Plain JSON, not JSONL: a document is loaded whole and
small (~2000 entries for `server`); the same call `gamedata.json/` made
(commit `da6d907`).

JSON content rules. Every value takes the JSON type that fits the data;
adapting a value to a format (a TSV cell, an upstream dump's spelling) is a
view's job, never the store's. Also: no addresses (ASLR makes them differ per
run); flags as names, unknown bits as `flag_<n>`; a convar's values decoded by
its `EConVarType` (`registration-flow.md`): a float32 as the shortest decimal
that reads back as the same float32, a color as four ints, a vector as a list
of floats, an absent value as `null`. Every type decodes, so bytes that don't
fit their type fail the dump (`validation.md`, "Shape") rather than being kept
as hex.

The `convars` and `concommands` aggregates have one row per declaration,
lossless and diffable; a DLL's patch shows as its rows. Columns, convars:
module, name, type, version, default, min, max, flags, help; commands: module,
name, flags, help. An absent value is `\N`. Rows the engine never shows make a
diff slightly over-sensitive, never blind.

Queue position is never stored as a value, in the JSON or the TSV: it is
position. A document's list is in queue order, and an aggregate's rows are
sorted by module, then in queue order, so a row's ordinal among its module's
rows is its queue index, and a test checks the two match. Queue order follows
link order, so a stored index would make one declaration added early in a DLL
renumber every later row (~1000 in `server.dll`); as position, it is one
added row. Order changes still show, as moved rows.

Reading views render the aggregates for people, local and uncommitted:
`data/convars.md` and `data/concommands.md` (help pages, per module, by
name) and
`data/dlls/load.tree.txt` (who loads whom). A per-DLL overview,
`data/dlls.tsv` (one row per DLL, scalars joined across facets), is a later
view, built when a question needs it.

The engine's merged view ("as the engine sees it") is a later, separate view
over the same JSON. It derives from the declarations but they can't be
recovered from it: the registry keeps one entry per name.

Registration's own flag changes are known: the per-DLL flag, except on a
`reference` declaration, which loses `developmentonly defensive` instead
(6860, `registration-flow.md`; checked by `validation.md`'s registry readback,
which compares only the names a DLL declares once).

> [!QUESTION] The merge rule for a name declared more than once, needed by
> that view. DumpSource2's `MergeQueued` OR's flags except
> `cheat|replicated|dontrecord|archive|per_user`
> (later declaration wins) and takes the first default/min/max/help; tier0's
> own conflict warnings (strings beside `VEngineCvar007`, 6851) say "parent
> wins" on help, on default, and on conflicting `CHEAT`/`REPLICATED`/
> `DONTRECORD`/`ARCHIVE`/`PER_USER` flags. Take the rule from tier0, checked
> against its registry (`capture-approach.kb/icvar-hook.md`), not from
> DumpSource2. Whether the view spans all DLLs or a dedicated server's set (no
> `client.dll`) is the user's call; all DLLs with a module column is the
> default, a server-only view being a filter of it.
