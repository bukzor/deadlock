# Which DLLs: every one in the install

Each DLL statically links its own reg-list (`registration-flow.md` step 2), so
any DLL might carry a queue. The store covers every `*.dll` under `game/`: 97
on 6860, all in `game/bin/win64` (incl. `qt5_plugins/`, `subtools/`) and
`game/citadel/bin/win64`. It comes from the directory walk, never a hand list.

Which DLLs carry queues is a fact the store answers, not a filter applied
before it. Every DLL that yields a queue is tier0 or loads it; the rest (Qt,
v8, ffmpeg, Steam, GPU vendor libraries) don't. Tools-only DLLs
(`resourcecompiler`, `physicsbuilder`, `visbuilder`…) are covered by the same
rule; a view can filter on the module column.

Each DLL is loaded in its own process, with a timeout. Four tools DLLs
(`helpsystem`, `assetpreview`, `propertyeditor`, `toolframework2`) hang inside
`LoadLibrary` every time (6851): one thread, ~0.2 s CPU, and the process
survives `taskkill /F` and `Stop-Process -Force`.

The `load` facet (`output-views.md`) records every DLL's outcome: `ok`, with
the modules the load added (system DLLs included, so the list varies with
the Windows build); `failed`, with the error (`vfx_dx11` and `phonon4`
on 6860, `LoadLibraryExW: 126`, a dependency not found); or `excluded`, with
its reason. Excluded DLLs (`deadlock.dll_load.EXCLUDED`, WSL-side) are never
loaded, since a hung load leaves an unkillable process behind. A timeout fails
the build, and the fix is a new exclusion. A DLL that loads and yields no
queue is accepted: on 6860, 8 of the 43 `ok` DLLs whose load includes tier0
(`bugreporter_filequeue`, `netgraph_subtool`, `p4lib`, `panorama_text_pango`,
`soundviewer_subtool`, `valve_avi`, `valve_webm`, `valve_wmf`). Each scan
observes that, rather than failing to find a queue: none of the 8 allocates a
queue block while loading (`capture-approach.kb/allocator-hook.md`).

Loading a DLL also loads its imports, so a DLL importing an excluded one
would hang too. None does: on 6860, the static plus delay-import closure of
every other DLL reaches no excluded one (`deadlock.dll_load.EXCLUDED`).

> [!TODO] Record only the added modules whose files are in the install.
> The rest are the host's (the OS's closure of system DLLs, or the
> interpreter's), and a DLL's direct system imports are the PE import
> table's to record, deterministically, in the planned `pe` facet
> (`output-views.md`). What would change this: a question about the
> runtime system closure that the import table can't answer.
