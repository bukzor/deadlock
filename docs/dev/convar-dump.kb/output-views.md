# Output: a lossless store of data about the DLLs; views derived from it

Per `../decisions.kb/commit-diffable-data-let-git-diff.md`, shaped like the
existing `gamedata` pipeline (`gamedata.list` → `gamedata.json/` →
`gamedata.tsv/`). Convars and concommands are the first purpose, not the
store's shape. A **facet** is one side of a DLL that one producer dumps (its
file, its load, its convar queue); each facet is dumped losslessly for every
DLL, and a purpose is a filter or view over the store, so the store stays
valid for the next question about DLLs.

> [!TODO] The layout, facet-first under one root, one process per (facet, DLL):
>
> - `data/dlls.list` (gitignored, like `gamedata.list`): membership only, every
>   `*.dll` under `game/`, one path per line relative to `game/`. DLL basenames
>   are unique (97 DLLs, 6860), so a basename keys everything below. Nothing
>   that changes on a patch goes here: every atom depends on this file, so a
>   size or hash in it would re-run them all.
> - `data/dlls/<facet>/default.json.do` (gitignored: near-verbatim Valve data):
>   one facet of one DLL → one JSON document; `$2` is the basename. Guard: the
>   name must be in `dlls.list`, and for a load-time facet `load/<dll>.json`
>   must say `ok`; anything else fails loudly. No input but the DLL and the
>   pinned build knowledge, so atoms are independent and `redo -j` runs them in
>   parallel. Process overhead is ~0.2 s per atom (6860,
>   `../probes/load_time.py`).
> - `data/dlls/default.tsv.do`: a case table on the facet, as
>   `gamedata.dense.tsv/default.tsv.do` has. Each calls `redo-ifchange` once
>   over its facet's documents (one call, so redo parallelises), then runs a
>   WSL-side `deadlock.dlls_<facet>` module with tests, writing `<facet>.tsv`, the
>   facet's lossless aggregate. Committed per facet; `convars.tsv` and
>   `concommands.tsv` are.

> [!TODO] The first facets: `file` (size, sha256), `load` (outcome: `ok` with
> the modules the load pulled in, `failed` with the error, or `excluded` with
> its reason; `dll-coverage.md`), `convars`, `concommands`. Later: `pe` (static
> PE metadata; relocations and `.pdata` as count + hash, the rest whole: 14 MB
> for all 97 in `pefile`'s own shape, 6860, `../probes/pe_size.py`),
> `interfaces` (the `InterfaceReg` list), logging channels, schemas.

A `convars` or `concommands` document is the lossless record of one queue: a
list in queue order, every declaration kept, duplicates included: on 6854
`server.dll` alone declares `developer` and three `citadel_*_reveal_duration`
more than once (2008 declarations, 2003 names). Commands are their own facet,
not convars: separate creation struct, queue, registration slot and registry
(`registration-flow.md`). Plain JSON, not JSONL: a document is loaded whole and
small (~2000 entries for `server`); the same call `gamedata.json/` made
(commit `da6d907`).

> [!TODO] JSON content rules: no addresses (ASLR makes them differ per run);
> each entry carries its queue index; flags as names, unknown bits as
> `flag_<n>`; values decoded by type, anything undecodable kept as hex, never
> dropped.

> [!TODO] The `convars` and `concommands` aggregates: one row per declaration,
> sorted by (name, module, index), lossless and diffable; a DLL's patch shows
> as its rows. Columns, convars: name, module, index, type, default, min, max,
> flags, help; commands: name, module, index, flags, help. Rows the engine
> never shows make a diff slightly over-sensitive, never blind.

> [!QUESTION] The aggregates' `index` column. Queue position follows link
> order, so one declaration added early in a DLL shifts every later index in
> it (~1000 changed rows for one change in `server.dll`), which breaks "one
> meaningful change ≈ one changed line". Proposed: the name's occurrence within
> its DLL (0 first, 1 its first duplicate) in the TSV, the queue index kept in
> the JSON. Settle before the first commit: past builds can't be re-rendered,
> since Steam overwrites the DLLs and the JSON is gitignored.

A per-DLL overview, `data/dlls.tsv` (one row per DLL, scalars joined across
facets), is a later view, built when a question needs it.

The engine's merged view ("as the engine sees it") is a later, separate view
over the same JSON. It derives from the declarations but they can't be
recovered from it: the registry keeps one entry per name.

> [!QUESTION] The merge rule, and tier0's flag changes at registration, needed
> by that view. Known on 6854 (`server.dll`): the registry adds the per-DLL flag
> (`gamedll`, 0x4) to 1978 declarations, `developmentonly|defensive` to 20
> instead (s2sdk's `SanitiseConVarFlags`), something else to 5. DumpSource2's
> `MergeQueued` OR's flags except `cheat|replicated|dontrecord|archive|per_user`
> (later declaration wins) and takes the first default/min/max/help; tier0's
> own conflict warnings (strings beside `VEngineCvar007`, 6851) say "parent
> wins" on help, on default, and on conflicting `CHEAT`/`REPLICATED`/
> `DONTRECORD`/`ARCHIVE`/`PER_USER` flags. Take the rule from tier0, checked
> against its registry (`capture-approach.kb/icvar-hook.md`), not from
> DumpSource2. Whether the view spans all DLLs or a dedicated server's set (no
> `client.dll`) is the user's call; all DLLs with a module column is the
> default, a server-only view being a filter of it.
