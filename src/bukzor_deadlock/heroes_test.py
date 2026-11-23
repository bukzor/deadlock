import pytest

from .heroes import attrs, columns, render, stats

HEROES = {
    "hero_base": {
        "m_mapStartingStats": {"EMaxHealth": 780.0, "EStamina": 3},
        "m_bDisabled": False,
    },
    "hero_a": {
        "m_mapStartingStats": {"EMaxHealth": 830.0, "EStamina": 3, "EMeleeResist": 0.1},
        "m_HeroID": 7,
        "m_bDisabled": True,
        "m_bPlayerSelectable": True,
        "m_strModelName": "models/heroes_wip/a/a.vmdl",
        "m_colorUI": [142],
    },
    "generic_data_type": "CCitadelHeroData",
    "_include": ["scripts/other.vdata"],
}

NAMES = {"hero_a:n": "Amber"}


class DescribeStats:
    def it_collects_per_hero_starting_stats_ignoring_other_entries(self):
        assert stats(HEROES) == {
            "hero_base": {"EMaxHealth": 780.0, "EStamina": 3},
            "hero_a": {"EMaxHealth": 830.0, "EStamina": 3, "EMeleeResist": 0.1},
        }

    def it_requires_every_hero_to_define_all_base_stats(self):
        missing = {"hero_base": {"EMaxHealth": 780.0}, "hero_a": {"EStamina": 3}}
        with pytest.raises(AssertionError, match="hero_a"):
            _ = columns(missing)


class DescribeAttrs:
    def it_collects_only_the_listed_identity_and_status_fields(self):
        assert attrs(HEROES) == {
            "hero_base": {"disabled": False},
            "hero_a": {"id": 7, "disabled": True, "player_selectable": True},
        }


class DescribeColumns:
    def it_is_the_sorted_union_of_every_stat(self):
        assert columns(stats(HEROES)) == ["EMaxHealth", "EMeleeResist", "EStamina"]


class DescribeRender:
    def it_leads_with_identity_then_stats_blank_where_absent(self):
        assert render(stats(HEROES), attrs(HEROES), NAMES) == (
            "hero\tname\tid\tdisabled\tin_development\tplayer_selectable"
            "\tlimited_testing\tneeds_testing\tprerelease_only"
            "\tassigned_players_only\tcomplexity"
            "\tEMaxHealth\tEMeleeResist\tEStamina\n"
            "hero_a\tAmber\t7\ttrue\t\ttrue\t\t\t\t\t\t830.0\t0.1\t3\n"
            "hero_base\t\t\tfalse\t\t\t\t\t\t\t\t780.0\t\t3\n"
        )
