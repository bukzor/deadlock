# Output: a comprehensive dump per DLL; TSV views derived from it

Per `../decisions.kb/commit-diffable-data-let-git-diff.md`, shaped like the
existing `gamedata` pipeline (`gamedata.list` → `gamedata.json/` →
`gamedata.tsv/`). Agreed with the user 2026-11-05.

> [!TODO] The layout:
>
> - `data/dlls.list` (gitignored, like `gamedata.list`): every DLL in scope
>   (`dll-coverage.md`) minus the exclusion list, one path per line relative to
>   `game/`. DLL basenames are unique across `bin/win64` and
>   `citadel/bin/win64` (6854), so a basename keys everything below.
> - `data/dlls.json/default.json.do` (gitignored: near-verbatim Valve data): one
>   DLL → one JSON document, from the Windows-side scanner
>   (`windows-python-host.md`) on stdout. Guard: the name must be in
>   `dlls.list`; anything else fails loudly. One process per DLL, no input but
>   the DLL and the pinned build knowledge, so targets are independent and
>   `redo -j` runs them in parallel.
> - `data/dlls.tsv/default.tsv.do` (committed `*.tsv`): a case table of views,
>   as `gamedata.tsv/default.tsv.do` has. Each view calls `redo-ifchange` once
>   over every `dlls.json/<dll>.json` named in `dlls.list` (one call, so redo
>   parallelises), then runs a WSL-side `deadlock.<view>` module with tests.
>   First views: `convars.tsv`, `concommands.tsv`.

The per-DLL JSON is the lossless record and grows by sections: `convars` and
`concommands` first, later interfaces, logging channels, schemas as needed. Each section is a
list in queue order, every declaration kept, duplicates included: on 6854
`server.dll` alone declares `developer` and three `citadel_*_reveal_duration`
more than once (2008 declarations, 2003 names). Plain JSON, not JSONL: it is
loaded whole, small (~2500 entries for `server`), and its sections have
different shapes; the same call `gamedata.json/` made (commit `da6d907`).

> [!TODO] JSON content rules: no addresses (ASLR makes them differ per run);
> each entry carries its queue index; flags as names, unknown bits as
> `flag_<n>`; values decoded by type, anything undecodable kept as hex, never
> dropped. Commands are their own section, not convars: separate creation
> struct, queue, registration slot and registry (`registration-flow.md`).

> [!TODO] Views: one row per declaration, sorted by (name, module, index),
> lossless and diffable; a DLL's patch shows as its rows. Columns, convars:
> name, module, index, type, default, min, max, flags, help; commands: name,
> module, index, flags, help. Rows the engine never shows make a diff slightly
> over-sensitive, never blind.

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
