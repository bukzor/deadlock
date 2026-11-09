# Walk the real cvar system after Connect (declined, unless the hook fails)

Connect the DLLs with the unmodified tier0 cvar system, then iterate
`FindFirstConVar`/`FindNextConVar` + `GetConVarData`, and the `…ConCommand`
equivalents (s2sdk `icvar.h`).

For: no hook at all; reads what the engine itself ended up believing.

Against: the registry has merged same-named declarations across DLLs (flags OR'd,
first default wins — DumpSource2 `MergeQueued` mirrors this), so per-DLL
attribution and the per-DLL completeness check (`../validation.md`) are lost. Needs
the same `Connect` as the hook, the iteration slots, and the `ConVarData` layout
instead of `ConVarCreation_t`.
