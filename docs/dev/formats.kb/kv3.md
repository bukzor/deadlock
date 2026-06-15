# KV3 (KeyValues3)

Valve's structured data format, the successor to KeyValues1. Used throughout
Source 2 for configuration and game data — in Deadlock the gameplay numbers live
in KV3 inside `vdata_c` resources (e.g. hero/ability data).

## Forms

- **Text KV3** — human-readable, with a `<!-- kv3 ... -->` header line declaring
  encoding and format GUIDs. What `Source2Viewer-CLI -d` emits when decompiling.
- **Binary KV3** — the `DATA` block of a compiled resource; several versioned
  encodings, optionally LZ4-compressed.

## Source of truth

In-process: the `keyvalues3` library reads both text and binary forms (binary
read-only for the newer compiled versions). For getting KV3 out of a compiled
`vdata_c` reliably, decompile with VRF first, then parse the text.
