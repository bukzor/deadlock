import pytest

from .heroes import columns, render, stats

RECORDS = [
    {"file": "scripts/heroes.vdata", "path": "hero_base.m_mapStartingStats.EMaxHealth", "value": 780.0},
    {"file": "scripts/heroes.vdata", "path": "hero_base.m_mapStartingStats.EStamina", "value": 3},
    {"file": "scripts/heroes.vdata", "path": "hero_a.m_mapStartingStats.EMaxHealth", "value": 830.0},
    {"file": "scripts/heroes.vdata", "path": "hero_a.m_mapStartingStats.EStamina", "value": 3},
    {"file": "scripts/heroes.vdata", "path": "hero_a.m_mapStartingStats.EMeleeResist", "value": 0.1},
    {"file": "scripts/abilities.vdata", "path": "ignored.path", "value": 1},
]


class DescribeStats:
    def it_collects_per_hero_starting_stats_ignoring_other_files(self):
        assert stats(RECORDS) == {
            "hero_base": {"EMaxHealth": 780.0, "EStamina": 3},
            "hero_a": {"EMaxHealth": 830.0, "EStamina": 3, "EMeleeResist": 0.1},
        }

    def it_requires_every_hero_to_define_all_base_stats(self):
        missing = {"hero_base": {"EMaxHealth": 780.0}, "hero_a": {"EStamina": 3}}
        with pytest.raises(AssertionError, match="hero_a"):
            columns(missing)


class DescribeColumns:
    def it_is_the_sorted_union_of_every_stat(self):
        assert columns(stats(RECORDS)) == ["EMaxHealth", "EMeleeResist", "EStamina"]


class DescribeRender:
    def it_emits_a_tsv_row_per_hero_blank_for_absent_stats(self):
        assert render(stats(RECORDS)) == (
            "hero\tEMaxHealth\tEMeleeResist\tEStamina\n"
            "hero_a\t830.0\t0.1\t3\n"
            "hero_base\t780.0\t\t3\n"
        )
