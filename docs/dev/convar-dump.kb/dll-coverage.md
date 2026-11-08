# Which DLLs: every one in the install

Each DLL statically links its own reg-list (`registration-flow.md` step 2), so
any DLL might carry a queue. The store covers every `*.dll` under `game/`: 97
on 6860, all in `game/bin/win64` (incl. `qt5_plugins/`, `subtools/`) and
`game/citadel/bin/win64`. It comes from the directory walk, never a hand list.

Which DLLs carry queues is a fact the store answers, not a filter applied
before it. Expected: the tier0 importers, plus tier0 itself (46 on 6851, 47
importers on 6860); the rest (Qt, v8, ffmpeg, Steam, GPU vendor libraries)
import nothing from tier0. Tools-only DLLs (`resourcecompiler`,
`physicsbuilder`, `visbuilder`…) are covered by the same rule; a view can
filter on the module column.

Each DLL is loaded in its own process, with a timeout. On 6851, four tools DLLs
(`helpsystem`, `assetpreview`, `propertyeditor`, `toolframework2`) hang inside
`LoadLibrary` every time: one thread, ~0.2 s CPU, and the process survives
`taskkill /F` and `Stop-Process -Force`. `vfx_dx11` fails to load (a dependency
isn't found).

> [!TODO] The `load` facet (`output-views.md`) records every DLL's outcome:
> `ok`, `failed` with the error (`vfx_dx11`), or `excluded` with its reason.
> Excluded DLLs are never loaded, since a hung load leaves an unkillable
> process behind; the list lives WSL-side. A timeout fails the build, and the
> fix is a new exclusion. A DLL that loads and yields no queue is accepted (6
> on 6851: `bugreporter_filequeue`, `p4lib`, `panorama_text_pango`,
> `valve_avi`, `valve_webm`, `valve_wmf`); shape alone can't tell that from a
> missed queue, so the oracle in `validation.md` is the backstop.

> [!QUESTION] Loading a DLL also loads its imports, so a DLL that imports an
> excluded one hangs anyway. The `load` record's module list shows the actual
> closure; whether any `ok`-candidate imports an excluded DLL is unchecked.
