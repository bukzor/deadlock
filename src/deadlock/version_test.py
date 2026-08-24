import pytest

from .version import fields, render

_INF = """\
ClientVersion=6684
ServerVersion=6684
SourceRevision=10933105
ProductName=citadel
VersionDate=Aug 22 2026
appID=1422450
"""


class DescribeFields:
    def it_parses_key_value_lines(self):
        assert fields(_INF.splitlines()) == {
            "ClientVersion": 6684,
            "ServerVersion": 6684,
            "SourceRevision": 10933105,
            "ProductName": "citadel",
            "VersionDate": "Aug 22 2026",
            "appID": "1422450",
        }

    def it_types_ordinals_as_ints_so_they_sort_and_subtract(self):
        parsed = fields(["ClientVersion=6684", "SourceRevision=10933105"])
        revision, client = parsed["SourceRevision"], parsed["ClientVersion"]
        assert isinstance(revision, int) and isinstance(client, int)
        assert revision - client == 10926421

    def it_keeps_int_shaped_ids_as_strings_because_arithmetic_is_meaningless(self):
        assert fields(["appID=1422450", "ToolsAppID=211"]) == {
            "appID": "1422450",
            "ToolsAppID": "211",
        }

    def it_skips_blank_lines(self):
        assert fields(["", "a=1", "\n"]) == {"a": "1"}

    def it_keeps_a_value_containing_an_equals_sign_intact(self):
        assert fields(["a=b=c"]) == {"a": "b=c"}

    def it_fails_loudly_on_a_non_assignment_line(self):
        with pytest.raises(AssertionError, match="bogus"):
            _ = fields(["bogus"])


class DescribeRender:
    def it_emits_key_sorted_one_key_per_line_json(self):
        assert render({"b": "2", "a": "1"}) == '{\n  "a": "1",\n  "b": "2"\n}\n'

    def it_emits_ordinals_unquoted(self):
        assert render({"ClientVersion": 6684}) == '{\n  "ClientVersion": 6684\n}\n'
