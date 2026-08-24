"""Exercises Source2Viewer-CLI against the real install.

Skips unless both the provisioned binary (`redo data/tools/Source2Viewer-CLI`)
and the game VPK exist.
"""

import pytest

from deadlock import paths, s2v

_VPK = paths.vpk_dir_file()
_BIN = s2v.binary_path()
_skip = pytest.mark.skipif(
    not (_VPK.exists() and _BIN.exists()),
    reason=f"need vpk ({_VPK}) and s2v ({_BIN})",
)


@_skip
class DescribeRun:
    def it_reports_a_version(self):
        result = s2v.run(["--version"])
        assert result.stdout.startswith("Version:"), result.stdout

    def it_lists_vpk_entries_with_crc(self):
        result = s2v.run(s2v.list_argv(_VPK))
        first = result.stdout.splitlines()[0]
        assert "CRC:" in first and "size:" in first, first
