import pytest

from .levels import Level, Row, canonical, curves, render, rows

HEROES = {
    "hero_base": {
        "m_mapLevelInfo": {
            "1": {"m_unRequiredGold": 0, "m_mapBonusCurrencies": {"EAbilityUnlocks": 1}},
            "2": {"m_unRequiredGold": 300, "m_mapBonusCurrencies": {"EAbilityPoints": 1}, "m_bUseStandardUpgrade": True},
        }
    },
    "hero_no_levels": {"m_bDisabled": True},
    "_include": ["scripts/other.vdata"],
}


class DescribeCurves:
    def it_builds_per_hero_level_maps_ignoring_other_entries(self):
        assert curves(HEROES) == {
            "hero_base": {
                1: Level(gold=0, bonus="unlock"),
                2: Level(gold=300, bonus="ap"),
            }
        }

    def it_fails_when_a_level_grants_two_bonuses(self):
        both = {"m_unRequiredGold": 0, "m_mapBonusCurrencies": {"EAbilityUnlocks": 1, "EAbilityPoints": 1}}
        with pytest.raises(AssertionError, match="hero_x"):
            _ = curves({"hero_x": {"m_mapLevelInfo": {"1": both}}})


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
