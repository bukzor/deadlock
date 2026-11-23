from collections.abc import Mapping
from pathlib import Path

import pytest
from bukzor_deadlock import gamedata, paths
from bukzor_deadlock.abilities import SIGNATURE, bindings
from pytest import approx

from . import casts
from .timeline import Cycle
from .types import BadRequest

HERO = "hero_x"
ABILITY = "ability_x"
TECH = {"_class": "scale_function_tech_damage", "m_flStatScale": 0.5, "m_eSpecificStatScaleType": "ETechPower"}


def tree(properties: Mapping[str, object], **entity: object) -> tuple[dict[str, object], dict[str, object]]:
    """``(heroes, abilities)``: one live hero binding ``ABILITY`` as a signature and ``gun`` as its weapon.

    A property given as ``None`` is left out.
    """
    slots = {"ESlot_Signature_1": ABILITY, "ESlot_Weapon_Primary": "gun"}
    heroes: dict[str, object] = {HERO: {"m_bDisabled": False, "m_mapBoundAbilities": slots}}
    props = {"AbilityCooldown": "10", "AbilityCastDelay": "0", **properties}
    wrapped: dict[str, object] = {k: v if isinstance(v, Mapping) else {"m_strValue": v} for k, v in props.items() if v is not None}
    abilities: dict[str, object] = {ABILITY: {"m_mapAbilityProperties": wrapped, **entity}, "gun": {}}
    return heroes, abilities


def cast(
    properties: Mapping[str, object], spirit: float = 0, tokens: Mapping[str, str] | None = None, **entity: object
) -> tuple[Cycle, tuple[str, ...]]:
    result = casts.cycle(*tree(properties, **entity), HERO, ABILITY, spirit, tokens or {})
    assert result is not None
    return result


def damages(cycle: Cycle) -> list[tuple[float, float, float, str]]:
    return [(h.trigger, h.land, h.damage, h.label) for h in cycle.hits]


class DescribeCycle:
    def it_lands_the_impact_at_the_cast_delay(self):
        cycle, _ = cast({"Damage": "100", "AbilityCastDelay": "0.25"})
        assert damages(cycle) == [(0, 0.25, 100, "Damage")]

    def it_repeats_every_cooldown(self):
        cycle, _ = cast({"Damage": "100", "AbilityCooldown": 12.5})
        assert cycle.period == 12.5

    def it_idles_for_the_cooldown_left_after_the_last_land(self):
        cycle, _ = cast({"Damage": "100", "DPS": "10", "AbilityDuration": "2", "TickRate": "1", "AbilityCastDelay": "0.5"})
        assert cycle.downtime == approx(10 - 2.5)

    def it_happens_once_without_a_cooldown(self):
        cycle, notes = cast({"Damage": "100", "AbilityCooldown": "0"})
        assert (cycle.period, cycle.downtime) == (None, 0)
        assert any("no cooldown" in n for n in notes), notes

    class WhenTheDamageOutlastsTheCooldown:
        def it_has_no_downtime_and_says_casts_overlap(self):
            cycle, notes = cast({"DPS": "10", "AbilityDuration": "12", "TickRate": "1"})
            assert cycle.downtime == 0
            assert any("outlast" in n and "12" in n and "10" in n for n in notes), notes

    def it_drops_a_zero_damage_hit(self):
        cycle, _ = cast({"Damage": "0", "DPS": "10", "AbilityDuration": "1", "TickRate": "1"})
        assert [h.label for h in cycle.hits] == ["DPS tick 1"]

    def it_drops_zero_dps_ticks(self):
        cycle, _ = cast({"Damage": "10", "DPS": "0", "AbilityDuration": "1", "TickRate": "1"})
        assert [h.label for h in cycle.hits] == ["Damage"]

    class WhenNotACast:
        def it_returns_none_for_the_gun(self):
            assert casts.cycle(*tree({"Damage": "1"}), HERO, "gun", 0, {}) is None

        def it_returns_none_for_another_heros_ability(self):
            assert casts.cycle(*tree({"Damage": "1"}), "hero_y", ABILITY, 0, {}) is None

        def it_returns_none_without_damage_or_dps(self):
            assert casts.cycle(*tree({"ImpactDamage": "1"}), HERO, ABILITY, 0, {}) is None

    class WhenTicking:
        def it_ticks_dps_every_tick_rate_across_the_duration(self):
            cycle, _ = cast({"DPS": "40", "AbilityDuration": "1", "TickRate": "0.5", "AbilityCastDelay": "0.1"})
            assert [h.label for h in cycle.hits] == ["DPS tick 1", "DPS tick 2"]
            assert [(h.land, h.damage) for h in cycle.hits] == [approx((0.6, 20)), approx((1.1, 20))]

        def it_triggers_each_tick_at_the_previous_land_and_the_first_at_the_cast(self):
            cycle, _ = cast({"DPS": "40", "AbilityDuration": "1.5", "TickRate": "0.5", "AbilityCastDelay": "0.1"})
            assert [(h.trigger, h.land) for h in cycle.hits] == [approx((0, 0.6)), approx((0.6, 1.1)), approx((1.1, 1.6))]

        def it_falls_back_to_the_channel_time(self):
            cycle, notes = cast({"DPS": "40", "AbilityDuration": "0", "AbilityChannelTime": "2", "TickRate": "1"})
            assert len(cycle.hits) == 2
            assert len(notes) == 1, notes  # only the unverified caveat

        def it_falls_back_to_another_tick_interval(self):
            cycle, notes = cast({"DPS": "40", "AbilityDuration": "1", "DamageInterval": "0.25"})
            assert len(cycle.hits) == 4
            assert len(notes) == 1, notes  # only the unverified caveat

        def it_leaves_dps_unmodeled_without_a_duration(self):
            cycle, notes = cast({"DPS": "40", "AbilityDuration": "0", "TickRate": "1", "BurnDuration": "3"})
            assert cycle.hits == ()
            assert any("not included" in n and "duration" in n for n in notes), notes

        def it_leaves_dps_unmodeled_without_a_tick_interval(self):
            cycle, notes = cast({"DPS": "40", "AbilityDuration": "1"})
            assert cycle.hits == ()
            assert any("Damage over time" in n and "tick interval" in n for n in notes), notes

    class WhenScaling:
        def it_adds_stat_scale_times_spirit(self):
            cycle, _ = cast({"Damage": {"m_strValue": "100", "m_subclassScaleFunction": TECH}}, spirit=10)
            assert cycle.hits[0].damage == approx(105)

        def it_treats_an_untyped_tech_damage_scale_as_spirit(self):
            scale = {"_class": "scale_function_tech_damage", "m_flStatScale": 2}
            cycle, _ = cast({"Damage": {"m_strValue": "100", "m_subclassScaleFunction": scale}}, spirit=10)
            assert cycle.hits[0].damage == approx(120)

        def it_notes_scaling_by_another_stat(self):
            scale = {"_class": "scale_function_single_stat", "m_flStatScale": 1, "m_eSpecificStatScaleType": "ELightMeleeDamage"}
            cycle, notes = cast({"Damage": {"m_strValue": "100", "m_subclassScaleFunction": scale}}, spirit=10)
            assert cycle.hits[0].damage == 100
            assert any("light melee damage" in n for n in notes), notes

    class WhenNoting:
        def it_says_last_that_the_model_is_not_yet_checked(self):
            _, notes = cast({"Damage": "1", "AbilityCharges": "2"})
            assert "Not yet checked in-game" in notes[-1], notes

        def it_orders_notes_by_how_much_they_move_the_numbers(self):
            tier = {"m_vecPropertyUpgrades": [{"m_strPropertyName": "AbilityCooldown", "m_strBonus": "-10"}]}
            flagged = {"m_strValue": "40", "m_bIsAbilityDamageProperty": True}
            props = {"Damage": "1", "ImpactDamage": flagged, "AbilityCharges": "2", "AbilityCooldown": "0"}
            _, notes = cast(props, m_vecAbilityUpgrades=[tier])
            starts = [n.split(" ")[0] for n in notes]
            assert starts == ["Extra", "Upgrades", "Charges", "This", "Not"], notes

        def it_notes_nothing_more_for_a_plain_cast(self):
            _, notes = cast({"Damage": "1"})
            assert len(notes) == 1, notes

        def it_notes_charges(self):
            _, notes = cast({"Damage": "1", "AbilityCharges": "2", "AbilityCooldownBetweenCharge": "7.5"})
            assert any("has 2," in n for n in notes), notes

        def it_ignores_zero_charges(self):
            _, notes = cast({"Damage": "1", "AbilityCharges": "0"})
            assert not any("charges" in n for n in notes), notes

        def it_notes_upgrades(self):
            tier = {"m_vecPropertyUpgrades": [{"m_strPropertyName": "Damage", "m_strBonus": "+40"}]}
            _, notes = cast({"Damage": "1"}, m_vecAbilityUpgrades=[tier])
            assert any("Upgrades not included" in n and "T1 damage +40" in n for n in notes), notes

        def it_names_upgrades_and_extra_damage_in_the_games_words(self):
            tier = {"m_vecPropertyUpgrades": [{"m_strPropertyName": "Damage", "m_strBonus": "+40"}]}
            flagged = {"m_strValue": "40", "m_bIsAbilityDamageProperty": True, "m_strLocTokenOverride": "Impact"}
            tokens = {"Damage_label": "Spirit Damage", "Impact_label": "Impact Damage"}
            _, notes = cast({"Damage": "1", "ImpactDamage": flagged}, tokens=tokens, m_vecAbilityUpgrades=[tier])
            assert any("T1 Spirit Damage +40" in n for n in notes), notes
            assert any("Extra damage not included: Impact Damage 40." in n for n in notes), notes

        def it_notes_each_unread_damage_property(self):
            flagged = {"m_strValue": "40", "m_bIsAbilityDamageProperty": True}
            _, notes = cast({"Damage": "1", "ImpactDamage": flagged, "BonusDamage": flagged})
            assert sum("Extra damage" in n for n in notes) == 2, notes

    class WhenParsing:
        def it_reads_numbers_and_numeric_strings(self):
            cycle, _ = cast({"Damage": 7.5, "AbilityCastDelay": ".2"})
            assert damages(cycle) == [(0, 0.2, 7.5, "Damage")]

        @pytest.mark.parametrize("value", ["0.1m", "40 30 20", "nan", "", True, None])
        def it_rejects_anything_else(self, value: object):
            with pytest.raises(BadRequest, match="AbilityCooldown"):
                _ = cast({"Damage": "1", "AbilityCooldown": value})


SCRIPTS = paths.data_dir() / "gamedata.json/scripts"



class DescribeCardDps:
    def it_is_the_dps_property_at_the_given_spirit(self):
        _, abilities = tree({"DPS": {"m_strValue": "20", "m_subclassScaleFunction": TECH}})
        assert casts.card_dps(abilities, ABILITY, spirit=10) == 25

    def it_is_none_without_a_dps_property(self):
        _, abilities = tree({"Damage": "100"})
        assert casts.card_dps(abilities, ABILITY, spirit=10) is None


def load(name: str) -> Mapping[str, object]:
    with Path(SCRIPTS / name).open() as file:
        return gamedata.load(file)


@pytest.mark.skipif(not SCRIPTS.is_dir(), reason=f"no local game data at {SCRIPTS}; build it with redo")
class DescribeRealData:
    def it_models_every_bound_signature_or_returns_none(self):
        heroes, abilities = load("heroes.json"), load("abilities.json")
        bound = [(hero, ability) for hero, slot, ability in bindings(heroes) if slot.startswith(SIGNATURE)]
        results = [casts.cycle(heroes, abilities, hero, ability, spirit=50, tokens={}) for hero, ability in bound]
        modeled = [r for r in results if r is not None]
        assert len(bound) > 100, len(bound)
        assert len(modeled) > len(bound) / 3, len(modeled)
        assert all(r[1][-1] == casts.HEURISTIC for r in modeled)
