# VPK v2 container

Deadlock's assets are packaged as a VPK v2 archive set: `pak01_dir.vpk` is the
directory/index, and `pak01_000.vpk` … `pak01_NNN.vpk` hold the file data
(Deadlock ships ~271 data archives). Confirmed against the real install.

## Header (`pak01_dir.vpk`, little-endian)

| offset | field | observed |
|--------|-------|----------|
| 0 | signature `uint32` | `0x55aa1234` |
| 4 | version `uint32` | `2` |
| 8 | tree size `uint32` | size of the directory tree that follows the header |

(v2 adds further section sizes after these — file-data/MD5/signature sections.)

## Directory tree

Nested NUL-terminated strings: for each `extension`, for each `path`, for each
`filename`, a directory entry follows (CRC32, preload bytes, archive index,
offset, length, `0xffff` terminator). An empty string ends each level; a single
space is the "none" placeholder for empty extension/path. The first entries seen
are `cfg/`, `panorama/citadel_keybinds`, etc.

The CRC32 stored per entry is what makes patch-diffing deterministic: comparing
two patches' `{path: crc}` maps yields exactly the added/removed/changed files.

## Source of truth

We read this via the `vpk` library, not by hand. `Source2Viewer-CLI --vpk_list`
emits the same `path CRC:… size:…` data directly.
