"""Minimal type stub for the parts of `vpk` we use."""

from collections.abc import Iterator

# directory entry: (preload, crc32, preload_length, archive_index,
# archive_offset, file_length) -- see vpk.VPK._make_meta_dict
_Meta = tuple[bytes, int, int, int, int, int]

class VPK:
    def read_index_iter(self) -> Iterator[tuple[str, _Meta]]: ...

def open(path: str) -> VPK: ...
