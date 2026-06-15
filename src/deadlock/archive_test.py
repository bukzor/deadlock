from .archive import Entry, manifest


def _entry(path: str, crc32: int = 0, file_length: int = 0) -> Entry:
    return Entry(
        path=path,
        crc32=crc32,
        file_length=file_length,
        preload_length=0,
        archive_index=0,
        archive_offset=0,
    )


class DescribeManifest:
    def it_renders_path_tab_crc_tab_size(self):
        text = manifest([_entry("a/b.vmdl_c", crc32=0x0A, file_length=42)])
        assert text == "a/b.vmdl_c\t0000000a\t42\n"

    def it_sorts_by_path_for_stable_diffs(self):
        text = manifest([_entry("z.txt"), _entry("a.txt"), _entry("m.txt")])
        assert text == "a.txt\t00000000\t0\nm.txt\t00000000\t0\nz.txt\t00000000\t0\n"

    def it_is_deterministic_regardless_of_input_order(self):
        entries = [_entry("b"), _entry("a")]
        assert manifest(entries) == manifest(reversed(entries))
