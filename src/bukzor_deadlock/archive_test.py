from .archive import Entry, manifest_records


def _entry(path: str, crc32: int = 0, file_length: int = 0) -> Entry:
    return Entry(
        path=path,
        crc32=crc32,
        file_length=file_length,
        preload_length=0,
        archive_index=0,
        archive_offset=0,
    )


class DescribeManifestRecords:
    def it_renders_path_crc_hex_and_size(self):
        assert manifest_records([_entry("a/b.vmdl_c", crc32=0x0A, file_length=42)]) == [
            {"path": "a/b.vmdl_c", "crc32": "0000000a", "size": 42}
        ]

    def it_sorts_by_path_for_stable_diffs(self):
        records = manifest_records([_entry("z"), _entry("a"), _entry("m")])
        assert [r["path"] for r in records] == ["a", "m", "z"]

    def it_is_deterministic_regardless_of_input_order(self):
        entries = [_entry("b", 1), _entry("a", 2)]
        assert manifest_records(entries) == manifest_records(list(reversed(entries)))
