# Source 2 compiled resource (`*_c`)

Files inside the paks ending in `_c` (e.g. `.vtex_c`, `.vmdl_c`, `.vdata_c`) are
*compiled* Source 2 resources: a generic block container wrapping type-specific
payloads. The uncompiled authoring forms drop the `_c` (`.vtex`, `.vmdl`, …).

## Shape

A resource is a header followed by a block table; each block has a 4-char type
and a byte range. Common blocks:

- `DATA` — the resource's main payload (often KV3; e.g. `vdata_c` game data).
- `RERL` — external resource references (dependencies on other files).
- `REDI` / `NTRO` — introspection/struct metadata describing how to read `DATA`.
- type-specific blocks (e.g. `VBIB` vertex/index buffers in models, `CTRL`/mip
  data in textures).

This is the layer that turns a compiled blob into a usable asset, and it tracks
engine changes closely (Deadlock-specific blocks appear here first).

## Source of truth

ValveResourceFormat implements this fully; we shell out to `Source2Viewer-CLI`
for decompilation (`-d`) and `--block DATA|RERL|REDI|NTRO|--all` to inspect raw
blocks. Do not reimplement the full container; only parse blocks directly via
`deadlock.binary` for needs VRF doesn't expose.
