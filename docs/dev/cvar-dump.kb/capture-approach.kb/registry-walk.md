# Walk the real cvar system after Init (declined, unless the hook fails)

`Connect` and `Init` the DLLs with the unmodified tier0 cvar system (the queue
replay runs in `Init`, `../registration-flow.md`), then iterate
`FindFirstConVar`/`FindNextConVar` + `GetConVarData`, and the `…ConCommand`
equivalents (s2sdk `icvar.h`).

For: no hook at all; reads what the engine itself ended up believing.

Against: the registry keeps one entry per name, merging same-named declarations
across DLLs by tier0's rule (still open, `../output-views.md`), so per-DLL
attribution and the per-DLL completeness check (`../validation.md`) are lost.
Needs the same `Connect` and `Init` as the hook, the iteration slots, and the
`ConVarData` layout instead of `ConVarCreation_t`.

Built as a check, not a capture: the registry readback (`../validation.md`) is
this walk, one DLL per process, after that DLL's `Init` (6860).
