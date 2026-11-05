# Which DLLs: every one that imports tier0

Each DLL statically links its own reg-list (`registration-flow.md` step 2), so
the in-scope set is every DLL under `game/bin/win64` and `game/citadel/bin/win64`
that imports `tier0.dll`, plus tier0 itself: 46 on 6851. It comes from the PE
import tables, never a hand list. The rest (Qt, v8, ffmpeg, Steam, GPU vendor
libraries) import nothing from tier0. Tools-only DLLs (`resourcecompiler`,
`physicsbuilder`, `visbuilder`…) are in scope by the same rule; a view can filter
on the module column.

Each DLL is loaded in its own process, with a timeout. On 6851, four tools DLLs
(`helpsystem`, `assetpreview`, `propertyeditor`, `toolframework2`) hang inside
`LoadLibrary` every time: one thread, ~0.2 s CPU, and the process survives
`taskkill /F` and `Stop-Process -Force`. `vfx_dx11` fails to load (a dependency
isn't found).

> [!TODO] An exclusion list, each entry with its reason, that the dumper skips
> without loading — a hung load leaves an unkillable process behind. Any other
> DLL that fails to load or times out fails the dump. A DLL that loads and
> yields no queue is accepted (6 on 6851: `bugreporter_filequeue`, `p4lib`,
> `panorama_text_pango`, `valve_avi`, `valve_webm`, `valve_wmf`); shape alone
> can't tell that from a missed queue, so the oracle in `validation.md` is the
> backstop.
