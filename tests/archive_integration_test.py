"""Exercises archive reading against the real Deadlock install.

Skips when the game files aren't present so the suite still passes on a bare
checkout / CI.
"""

import pytest

from deadlock import paths
from deadlock.archive import read_entries

_VPK = paths.vpk_dir_file()


@pytest.mark.skipif(not _VPK.exists(), reason=f"no game install at {_VPK}")
class DescribeReadEntries:
    def it_reads_a_large_realistic_entry_count(self):
        entries = list(read_entries(_VPK))
        assert len(entries) > 100_000, len(entries)

    def it_populates_crc_and_size_for_a_known_data_file(self):
        by_path = {e.path: e for e in read_entries(_VPK)}
        abilities = by_path["scripts/abilities.vdata_c"]
        assert abilities.crc32 != 0, abilities
        assert abilities.file_length > 0, abilities
