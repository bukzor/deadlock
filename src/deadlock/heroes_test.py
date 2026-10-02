import pytest

from .heroes import attrs, columns, render, stats

RECORDS = [
    {"path": "hero_base.m_mapStartingStats.EMaxHealth", "value": 780.0},
    {"path": "hero_base.m_mapStartingStats.EStamina", "value": 3},
    {"path": "hero_base.m_bDisabled", "value": False},
    {"path": "hero_a.m_mapStartingStats.EMaxHealth", "value": 830.0},
    {"path": "hero_a.m_mapStartingStats.EStamina", "value": 3},
    {"path": "hero_a.m_mapStartingStats.EMeleeResist", "value": 0.1},
    {"path": "hero_a.m_HeroID", "value": 7},
    {"path": "hero_a.m_bDisabled", "value": True},
    {"path": "hero_a.m_bPlayerSelectable", "value": True},
    {"path": "hero_a.m_strModelName", "value": "models/heroes_wip/a/a.vmdl"},
    {"path": "hero_a.m_colorUI[0]", "value": 142},
    {"path": "generic_data_type.m_bDisabled", "value": False},
]

NAMES = {"hero_a:n": "Amber"}


class DescribeStats:
    def it_collects_per_hero_starting_stats_ignoring_other_paths(self):
        assert stats(RECORDS) == {
            "hero_base": {"EMaxHealth": 780.0, "EStamina": 3},
            "hero_a": {"EMaxHealth": 830.0, "EStamina": 3, "EMeleeResist": 0.1},
        }

    def it_requires_every_hero_to_define_all_base_stats(self):
        missing = {"hero_base": {"EMaxHealth": 780.0}, "hero_a": {"EStamina": 3}}
        with pytest.raises(AssertionError, match="hero_a"):
            _ = columns(missing)


class DescribeAttrs:
    def it_collects_only_the_listed_identity_and_status_fields(self):
        assert attrs(RECORDS) == {
            "hero_base": {"disabled": False},
            "hero_a": {"id": 7, "disabled": True, "player_selectable": True},
        }


class DescribeColumns:
    def it_is_the_sorted_union_of_every_stat(self):
        assert columns(stats(RECORDS)) == ["EMaxHealth", "EMeleeResist", "EStamina"]


class DescribeRender:
    def it_leads_with_identity_then_stats_blank_where_absent(self):
        assert render(stats(RECORDS), attrs(RECORDS), NAMES) == (
            "hero\tname\tid\tdisabled\tin_development\tplayer_selectable"
            "\tlimited_testing\tneeds_testing\tprerelease_only"
            "\tassigned_players_only\tcomplexity"
            "\tEMaxHealth\tEMeleeResist\tEStamina\n"
            "hero_a\tAmber\t7\ttrue\t\ttrue\t\t\t\t\t\t830.0\t0.1\t3\n"
            "hero_base\t\t\tfalse\t\t\t\t\t\t\t\t780.0\t\t3\n"
        )
