from .diff import (
    ManifestDiff,
    diff_manifests,
    diff_records,
    format_diff,
    parse_manifest,
)


class DescribeParseManifest:
    def it_maps_path_to_crc_and_size(self):
        text = "a/b.vmdl_c\t0000000a\t42\nc.txt\t00000001\t9\n"
        assert parse_manifest(text) == {
            "a/b.vmdl_c": ("0000000a", 42),
            "c.txt": ("00000001", 9),
        }

    def it_ignores_blank_trailing_lines(self):
        assert parse_manifest("a\t00000000\t0\n\n") == {"a": ("00000000", 0)}


class DescribeDiffManifests:
    def it_finds_added_and_removed_paths(self):
        old = parse_manifest("keep\tAA\t1\ngone\tBB\t1\n")
        new = parse_manifest("keep\tAA\t1\nfresh\tCC\t1\n")
        result = diff_manifests(old, new)
        assert result.added == ["fresh"]
        assert result.removed == ["gone"]
        assert result.changed == []

    def it_flags_paths_whose_crc_changed(self):
        old = parse_manifest("f\tAA\t1\nsame\tDD\t1\n")
        new = parse_manifest("f\tBB\t2\nsame\tDD\t1\n")
        result = diff_manifests(old, new)
        assert result.changed == ["f"]
        assert result.added == [] and result.removed == []

    def it_sorts_each_category(self):
        old = parse_manifest("")
        new = parse_manifest("z\tA\t1\na\tA\t1\nm\tA\t1\n")
        assert diff_manifests(old, new).added == ["a", "m", "z"]

    def it_reports_no_changes_for_identical_manifests(self):
        m = parse_manifest("x\tAA\t1\n")
        assert diff_manifests(m, m) == ManifestDiff(added=[], removed=[], changed=[])


class DescribeFormatDiff:
    def it_prefixes_with_plus_minus_tilde_interleaved_by_path(self):
        result = ManifestDiff(added=["b"], removed=["a"], changed=["c"])
        assert format_diff(result) == "- a\n+ b\n~ c\n"


class DescribeDiffRecords:
    def it_describes_each_change_as_a_jsonl_ready_dict(self):
        old = parse_manifest("gone\tBB\t1\nf\tAA\t1\n")
        new = parse_manifest("fresh\tCC\t2\nf\tDD\t3\n")
        assert diff_records(old, new) == [
            {"change": "changed", "path": "f", "old_crc32": "AA", "new_crc32": "DD"},
            {"change": "added", "path": "fresh", "crc32": "CC"},
            {"change": "removed", "path": "gone", "crc32": "BB"},
        ]
