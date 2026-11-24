import struct
import zlib
from pathlib import Path

import pytest

from .archive import Entry
from . import explode
from .explode import (
    EMBEDDED,
    RESERVE,
    Member,
    archive_file,
    check_room,
    main,
    select,
    write_tree,
)


def _entry(
    path: str, archive_index: int = 0, archive_offset: int = 0, data: bytes = b""
) -> Entry:
    return Entry(
        path=path,
        crc32=zlib.crc32(data),
        file_length=len(data),
        preload_length=0,
        archive_index=archive_index,
        archive_offset=archive_offset,
    )


class DescribeSelect:
    def it_takes_everything_for_the_empty_dir(self):
        entries = [_entry("a/b.txt"), _entry("c.txt")]
        assert [m.rel for m in select(entries, "")] == ["a/b.txt", "c.txt"]

    def it_keeps_only_entries_below_the_dir_relative_to_it(self):
        entries = [_entry("sounds/vo/a/x.vsnd_c"), _entry("sounds/vox.txt")]
        assert [m.rel for m in select(entries, "sounds/vo")] == ["a/x.vsnd_c"]

    def it_orders_by_archive_then_offset_for_sequential_reads(self):
        entries = [_entry("a", 1, 0), _entry("b", 0, 9), _entry("c", 0, 3)]
        assert [m.rel for m in select(entries, "")] == ["c", "b", "a"]

    def it_refuses_preload_bytes_it_cannot_read(self):
        entry = Entry("a", 0, 0, preload_length=4, archive_index=0, archive_offset=0)
        with pytest.raises(AssertionError, match="'a'"):
            _ = select([entry], "")

    def it_fails_loudly_when_nothing_matches(self):
        with pytest.raises(AssertionError, match="nope"):
            _ = select([_entry("a/b")], "nope")


class DescribeCheckRoom:
    def it_allows_a_write_that_leaves_the_reserve_free(self):
        check_room(need=10, free=10 + RESERVE)

    def it_refuses_a_write_that_would_eat_into_the_reserve(self):
        with pytest.raises(AssertionError, match="reserve"):
            check_room(need=11, free=10 + RESERVE)


class DescribeArchiveFile:
    def it_names_the_numbered_data_archive_beside_the_dir_file(self):
        assert archive_file(Path("/g/pak01_dir.vpk"), 7) == Path("/g/pak01_007.vpk")

    def it_reads_embedded_data_from_the_dir_file_itself(self):
        dir_file = Path("/g/pak01_dir.vpk")
        assert archive_file(dir_file, EMBEDDED) == dir_file


def _pak(tmp_path: Path, blobs: list[bytes]) -> tuple[Path, list[Entry]]:
    """One data archive holding ``blobs`` back to back, and their entries."""
    dir_file = tmp_path / "pak01_dir.vpk"
    _ = (tmp_path / "pak01_000.vpk").write_bytes(b"".join(blobs))
    offsets = [sum(len(b) for b in blobs[:i]) for i in range(len(blobs))]
    entries = [
        _entry(f"d/f{i}.bin", 0, off, blob)
        for i, (off, blob) in enumerate(zip(offsets, blobs))
    ]
    return dir_file, entries


class DescribeWriteTree:
    def it_writes_each_members_bytes_at_its_relative_path(self, tmp_path: Path):
        dir_file, entries = _pak(tmp_path, [b"hello", b"world!"])
        out = tmp_path / "out"
        write_tree(dir_file, select(entries, "d"), out)
        assert (out / "f0.bin").read_bytes() == b"hello"
        assert (out / "f1.bin").read_bytes() == b"world!"

    def it_fails_loudly_on_a_crc_mismatch(self, tmp_path: Path):
        dir_file, [entry] = _pak(tmp_path, [b"hello"])
        bad = Member(entry=Entry("d/f0.bin", 0, 5, 0, 0, 0), rel="f0.bin")
        assert bad.entry.crc32 != entry.crc32
        with pytest.raises(AssertionError, match="f0.bin"):
            write_tree(dir_file, [bad], tmp_path / "out")


def _embedded_vpk(files: dict[tuple[str, str, str], bytes]) -> bytes:
    """A VPK v1 dir file whose data all follows the index.

    Each entry gets its own extension group: ext, path, name, then the
    18-byte entry and the name- and path-list terminators.
    """
    tree, data = b"", b""
    for (ext, path, name), blob in files.items():
        crc = zlib.crc32(blob)
        meta = struct.pack("<IHHIIH", crc, 0, EMBEDDED, len(data), len(blob), 0xFFFF)
        tree += b"\0".join(s.encode() for s in (ext, path, name)) + b"\0" + meta
        tree += b"\0\0"
        data += blob
    tree += b"\0"
    return struct.pack("<3I", 0x55AA1234, 1, len(tree)) + tree + data


class DescribeMain:
    def it_explodes_a_real_vpk_with_embedded_data(self, tmp_path: Path):
        dir_file = tmp_path / "pak01_dir.vpk"
        files = {("txt", "sub", "a"): b"alpha", ("txt", " ", "b"): b"beta"}
        _ = dir_file.write_bytes(_embedded_vpk(files))
        main(["explode", str(dir_file), str(tmp_path / "out"), "sub"])
        assert sorted(p.name for p in (tmp_path / "out").rglob("*")) == ["a.txt"]
        assert (tmp_path / "out/a.txt").read_bytes() == b"alpha"

    def it_refuses_before_writing_when_the_disk_lacks_room(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ):
        dir_file = tmp_path / "pak01_dir.vpk"
        _ = dir_file.write_bytes(_embedded_vpk({("txt", "sub", "a"): b"alpha"}))
        monkeypatch.setenv("DEADLOCK_FREE_SPACE_DIR", str(tmp_path))
        monkeypatch.setattr(explode, "RESERVE", 10**18)
        with pytest.raises(AssertionError, match="reserve"):
            main(["explode", str(dir_file), str(tmp_path / "out"), "sub"])
        assert not (tmp_path / "out").exists()
