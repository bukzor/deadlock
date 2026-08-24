import pytest

from .levels import Level, Row, canonical, curves, render, rows

RECORDS = [
    {"path": "hero_base.m_mapLevelInfo.1.m_unRequiredGold", "value": 0},
    {"path": "hero_base.m_mapLevelInfo.1.m_mapBonusCurrencies.EAbilityUnlocks", "value": 1},
    {"path": "hero_base.m_mapLevelInfo.2.m_unRequiredGold", "value": 300},
    {"path": "hero_base.m_mapLevelInfo.2.m_mapBonusCurrencies.EAbilityPoints", "value": 1},
    {"path": "hero_base.m_mapLevelInfo.2.m_bUseStandardUpgrade", "value": True},
    {"path": "ignored.path", "value": 1},
]


class DescribeCurves:
    def it_builds_per_hero_level_maps_ignoring_other_paths(self):
        assert curves(RECORDS) == {
            "hero_base": {
                1: Level(gold=0, bonus="unlock"),
                2: Level(gold=300, bonus="ap"),
            }
        }


class DescribeCanonical:
    def it_returns_the_shared_curve(self):
        base = {1: Level(gold=0, bonus="unlock")}
        assert canonical({"hero_base": base, "hero_a": dict(base)}) == base

    def it_raises_when_a_hero_diverges(self):
        with pytest.raises(AssertionError, match="hero_a"):
            _ = canonical(
                {
                    "hero_base": {1: Level(gold=0, bonus="unlock")},
                    "hero_a": {1: Level(gold=99, bonus="unlock")},
                }
            )


class DescribeRows:
    def it_adds_starting_souls_renumbers_from_zero_and_accumulates(self):
        curve = {
            1: Level(gold=0, bonus="unlock"),
            2: Level(gold=300, bonus="ap"),
            3: Level(gold=600, bonus="unlock"),
        }
        assert rows(curve) == [
            Row(level=0, souls=600, delta=0, ability=1, ap=0),
            Row(level=1, souls=900, delta=300, ability=1, ap=1),
            Row(level=2, souls=1200, delta=300, ability=2, ap=1),
        ]


class DescribeRender:
    def it_emits_zero_padded_tsv_with_header(self):
        assert render([Row(level=0, souls=600, delta=0, ability=1, ap=0)]) == (
            "level\tsouls\tdelta\tability\tAP\n00\t00600\t0000\t1\t00\n"
        )
