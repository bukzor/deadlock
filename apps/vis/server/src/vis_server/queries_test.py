from collections.abc import Mapping, Sequence

import pytest
from deadlock import paths
from pytest import approx

from .queries import QUERIES, GameData, listed, load_data, registry
from .types import BadRequest, JsonObj, Params

TECH = {"_class": "scale_function_tech_damage", "m_flStatScale": 0.5, "m_eSpecificStatScaleType": "ETechPower"}


def _props(**values: object) -> dict[str, object]:
    return {k: v if isinstance(v, Mapping) else {"m_strValue": v} for k, v in values.items()}


def _level(game: int) -> dict[str, object]:
    info: dict[str, object] = {"m_unRequiredGold": 100 * game, "m_mapBonusCurrencies": {"EAbilityPoints": 1}}
    return info if game == 1 else {**info, "m_bUseStandardUpgrade": True}


PER_BOON = {
    "MODIFIER_VALUE_BASE_BULLET_DAMAGE_FROM_LEVEL": 0.25,
    "MODIFIER_VALUE_BASE_MELEE_DAMAGE_FROM_LEVEL": 2.0,
    "MODIFIER_VALUE_TECH_POWER": 1.5,
}


def _hero(slots: Mapping[str, str], disabled: bool = False) -> dict[str, object]:
    """A hero whose last level is 3."""
    return {
        "m_bDisabled": disabled,
        "m_mapStartingStats": {"ELightMeleeDamage": 50, "EHeavyMeleeDamage": 116},
        "m_mapBoundAbilities": {f"ESlot_{slot}": ability for slot, ability in slots.items()},
        "m_mapLevelInfo": {str(game): _level(game) for game in range(1, 5)},
        "m_mapStandardLevelUpUpgrades": PER_BOON,
    }


GUN = {
    "m_flBulletDamage": 4.0, "m_iBullets": 1, "m_iBurstShotCount": 1, "m_flCycleTime": 0.5,
    "m_flIntraBurstCycleTime": 0.0, "m_iClipSize": 4, "m_reloadDuration": 2.0, "m_flRange": 7000.0,
    "m_flBulletSpeed": 10000 / 0.0254,  # 10000 m/s
}  # fmt: skip
ATTACK = {"m_flCooldownOnHit": 0.75, "m_flCooldownOnMiss": 0.75}
KIT = {"Weapon_Primary": "gun_a", "Weapon_Melee": "melee_a", "Signature_2": "buff", "Signature_1": "blast"}
DATA = GameData(
    heroes={
        "hero_c": _hero({"Weapon_Melee": "melee_a"}),
        "hero_a": _hero(KIT),
        "hero_off": _hero(KIT, disabled=True),
        "hero_dev": _hero(KIT),  # live, but not listed
    },
    abilities={
        "gun_a": {"m_mapWeaponInfos": {"primary": GUN}},
        "melee_a": {"m_mapAttacks": {"EAttackType_Light": ATTACK, "EAttackType_Heavy": ATTACK}},
        "blast": {"m_mapAbilityProperties": _props(Damage={"m_strValue": "100", "m_subclassScaleFunction": TECH},
                                                   AbilityCooldown="10", AbilityCastDelay="0.5")},
        "buff": {"m_mapAbilityProperties": _props(AbilityCooldown="20")},
    },  # fmt: skip
    listed={"hero_a": "Bravo", "hero_c": "Alpha", "hero_off": "Off"},
)
SYNTHETIC = registry(lambda: DATA)


def run(query: str, **params: str) -> Sequence[JsonObj]:
    return SYNTHETIC[query].run(params)


def kinds(lines: Sequence[JsonObj], kind: str) -> list[JsonObj]:
    return [line for line in lines if line["kind"] == kind]


def notes(lines: Sequence[JsonObj]) -> list[str]:
    return [str(line["text"]) for line in kinds(lines, "note")]


class DescribeRegistry:
    def it_offers_the_designs_queries_and_params(self):
        assert {name: set(q.params) for name, q in SYNTHETIC.items()} == {
            "heroes": set(),
            "abilities": {"hero"},
            "timeline": {"hero", "ability", "horizon", "level", "distance", "spirit", "windup", "hp"},
        }
        assert {name: set(q.params) for name, q in QUERIES.items()} == {
            name: set(q.params) for name, q in SYNTHETIC.items()
        }

    def it_loads_nothing_until_a_query_runs(self):
        def unloadable() -> GameData:
            raise AssertionError("loaded")

        queries = registry(unloadable)
        with pytest.raises(AssertionError, match="loaded"):
            _ = queries["heroes"].run({})

    @pytest.mark.parametrize("query", ["heroes", "abilities", "timeline"])
    def it_rejects_an_unknown_parameter(self, query: str):
        with pytest.raises(BadRequest, match="colour"):
            _ = run(query, hero="hero_a", ability="melee_light", colour="red")


class DescribeHeroes:
    def it_lists_each_live_listed_hero_by_display_name(self):
        assert run("heroes") == [{"hero": "hero_c", "name": "Alpha"}, {"hero": "hero_a", "name": "Bravo"}]


class DescribeListed:
    def it_names_each_hero_but_those_in_development_and_the_training_dummy(self):
        rows = [("hero_astro", "Holliday", "false"), ("hero_genericperson", "Generic Person", "true"), ("hero_targetdummy", "TargetDummy", "false")]
        assert listed({"hero": h, "name": n, "in_development": d} for h, n, d in rows) == {"hero_astro": "Holliday"}


class DescribeAbilities:
    def it_lists_the_gun_the_melees_then_the_signatures_in_slot_order(self):
        assert run("abilities", hero="hero_a") == [
            {"ability": "gun_a", "name": "gun_a", "kind": "gun"},
            {"ability": "melee_light", "name": "melee_light", "kind": "melee"},
            {"ability": "melee_heavy", "name": "melee_heavy", "kind": "melee"},
            {"ability": "blast", "name": "blast", "kind": "cast"},
            {"ability": "buff", "name": "buff", "kind": None},
        ]

    def it_lists_melee_alone_for_a_hero_without_a_gun_or_signatures(self):
        assert [line["ability"] for line in run("abilities", hero="hero_c")] == ["melee_light", "melee_heavy"]

    class WhenTheRequestIsBad:
        def it_rejects_a_missing_hero(self):
            with pytest.raises(BadRequest, match="hero"):
                _ = run("abilities")

        @pytest.mark.parametrize("hero", ["hero_z", "hero_off"])
        def it_rejects_a_hero_that_isnt_live(self, hero: str):
            with pytest.raises(BadRequest, match=hero):
                _ = run("abilities", hero=hero)


def timeline(ability: str = "melee_light", hero: str = "hero_a", **params: str) -> Sequence[JsonObj]:
    return run("timeline", hero=hero, ability=ability, **params)


def blast_timeline(props: Mapping[str, object], **params: str) -> Sequence[JsonObj]:
    """The timeline of ``hero_a``'s ``blast``, its properties replaced by ``props``."""
    data = GameData(DATA.heroes, {**DATA.abilities, "blast": {"m_mapAbilityProperties": _props(**props)}}, DATA.listed)
    return registry(lambda: data)["timeline"].run({"hero": "hero_a", "ability": "blast", **params})


class DescribeTimeline:
    def it_emits_hits_then_measures_then_notes(self):
        found = [str(line["kind"]) for line in timeline()]
        assert found == sorted(found, key=["cycle", "hit", "measure", "note"].index), found
        assert found[0] == "cycle" and set(found) == {"cycle", "hit", "measure", "note"}

    def it_emits_each_unrolled_hit(self):
        assert kinds(timeline(horizon="1.1", windup="0.25"), "hit") == [
            {"kind": "hit", "trigger": 0.0, "land": 0.25, "damage": 50.0, "label": "light melee", "cycle": 0},
            {"kind": "hit", "trigger": 0.75, "land": 1.0, "damage": 50.0, "label": "light melee", "cycle": 1},
        ]

    def it_unrolls_two_periods_by_default(self):
        assert [float(str(h["trigger"])) for h in kinds(timeline(), "hit")] == [0.0, 0.75]  # horizon: 2 periods of 0.75 s, so 2 cycles
        assert kinds(timeline("blast"), "cycle") == [{"kind": "cycle", "period": 10.0, "downtime": 9.5, "horizon": 20.0}]

    def it_unrolls_10_seconds_for_a_one_shot(self):
        [line] = kinds(blast_timeline({"Damage": "5", "AbilityCooldown": "0", "AbilityCastDelay": "0"}), "cycle")
        assert (line["period"], line["horizon"]) == (None, 10.0)

    def it_sends_only_hits_that_land_within_the_horizon(self):
        lands = [float(str(h["land"])) for h in kinds(timeline("blast", horizon="10.2"), "hit")]
        assert lands == [0.5]  # the second cast triggers at 10, lands at 10.5

    def it_emits_each_measure(self):
        measures = kinds(timeline(horizon="1"), "measure")
        names = ["steady_dps", "cycle_damage", "total_damage", "first_land"]
        assert [m["name"] for m in measures] == names  # a swing has no downtime: no uptime_dps
        assert measures[0] == {
            "kind": "measure", "name": "steady_dps", "label": "DPS", "value": approx(50 / 0.75),
            "unit": "damage/s", "check": measures[0]["check"],
        }  # fmt: skip
        assert all(set(m) == {"kind", "name", "label", "value", "unit", "check"} and m["check"] for m in measures)

    def it_shows_a_casts_card_dps_at_the_given_spirit_and_level(self):
        dot = {"DPS": {"m_strValue": "20", "m_subclassScaleFunction": TECH}, "AbilityDuration": "2", "TickRate": "1",
               "AbilityCooldown": "10", "AbilityCastDelay": "0"}  # fmt: skip
        [card] = [m for m in kinds(blast_timeline(dot, spirit="7", level="2"), "measure") if m["name"] == "card_dps"]
        assert card["value"] == approx(20 + 0.5 * (7 + 3))

    def it_shows_no_card_dps_for_a_cast_without_one(self):
        assert "card_dps" not in [m["name"] for m in kinds(timeline("blast"), "measure")]

    def it_notes_the_sources_caveats_and_level_zero(self):
        found = notes(timeline(windup="0.3"))
        assert any("wind-up" in n for n in found), found
        assert found[0].startswith("Hero level 0, no items"), found
        assert not any("boon" in n for n in found), found

    def it_states_the_level_and_what_its_boons_add(self):
        found = notes(timeline(level="2"))
        assert found[0].startswith("Hero level 2, no items"), found
        assert found[1].startswith("Level 2 is 2 boons:") and "+0.5 bullet damage" in found[1], found
        assert "+4 light" in found[1] and "+9.28 heavy melee" in found[1] and "+3 spirit power" in found[1], found
        assert "not checked in-game" in found[1], found

    def it_states_the_level_for_an_ability_with_no_damage_model(self):
        assert notes(timeline("buff", level="3"))[0].startswith("Hero level 3, no items"), notes(timeline("buff", level="3"))

    @pytest.mark.parametrize(
        ("ability", "param", "value", "field", "expected"),
        [
            ("gun_a", "distance", "50", "land", 0.005),
            ("melee_heavy", "windup", "0.4", "land", 0.4),
            ("blast", "spirit", "10", "damage", 105),
            ("gun_a", "level", "2", "damage", 4.5),
            ("melee_light", "level", "2", "damage", 54),
            ("melee_heavy", "level", "2", "damage", 116 + 4 * 116 / 50),
            ("blast", "level", "2", "damage", 100 + 0.5 * 3),
        ],
    )
    def it_passes_each_parameter_to_its_source(self, ability: str, param: str, value: str, field: str, expected: float):
        assert kinds(timeline(ability, **{param: value}), "hit")[0][field] == approx(expected)

    class WhenGivenHp:
        def it_measures_time_to_kill_first(self):
            [first, *_] = kinds(timeline(hp="100", windup="0.25"), "measure")
            assert (first["name"], first["value"]) == ("time_to_kill", 1.0)

        def it_stretches_the_default_horizon_to_the_time_to_kill(self):
            lines = timeline(hp="300", windup="0.25")  # the 6th swing lands at 4 s, in the 6th period of 0.75 s
            assert (kinds(lines, "cycle")[0]["horizon"], kinds(lines, "hit")[-1]["land"]) == (approx(4.5), approx(4.0))

        def it_notes_hp_not_reached_within_120_s(self):
            lines = timeline(hp="1e9")
            assert kinds(lines, "cycle")[0]["horizon"] == 120 and "within 120 s" in notes(lines)[-1], notes(lines)

        def it_notes_hp_not_reached_within_the_horizon(self):
            lines = timeline(hp="101", horizon="1", windup="0.3")
            assert "time_to_kill" not in [m["name"] for m in kinds(lines, "measure")]
            found = notes(lines)
            assert "101" in found[-1] and "1 s" in found[-1], found
            assert any("wind-up" in n for n in found[:-1]), found

        def it_says_nothing_of_hp_when_reached(self):
            assert not any("HP" in n for n in notes(timeline(hp="100", windup="0.25")))

    class WhenTheAbilityHasNoDamageModel:
        def it_emits_only_notes_saying_so(self):
            lines = timeline("buff")
            assert {str(line["kind"]) for line in lines} == {"note"}
            assert any("buff" in n and "no damage model" in n for n in notes(lines)), notes(lines)

    class WhenTheRequestIsBad:
        @pytest.mark.parametrize("missing", ["hero", "ability"])
        def it_rejects_a_missing_required_parameter(self, missing: str):
            params = {"hero": "hero_a", "ability": "melee_light"}
            del params[missing]
            with pytest.raises(BadRequest, match=missing):
                _ = run("timeline", **params)

        @pytest.mark.parametrize(("hero", "ability"), [("hero_z", "melee_light"), ("hero_off", "melee_light"),
                                                       ("hero_a", "nope"), ("hero_c", "gun_a")])  # fmt: skip
        def it_rejects_an_unknown_hero_or_ability(self, hero: str, ability: str):
            with pytest.raises(BadRequest, match=f"{hero}|{ability}"):
                _ = timeline(ability, hero)

        @pytest.mark.parametrize("value", ["ten", "", "nan", "inf", "-inf"])
        def it_rejects_a_value_that_isnt_a_finite_number(self, value: str):
            with pytest.raises(BadRequest, match="horizon"):
                _ = timeline(horizon=value)

        @pytest.mark.parametrize(
            ("param", "value"),
            [("horizon", "0"), ("horizon", "-1"), ("hp", "0"), ("distance", "-1"), ("spirit", "-1"), ("windup", "-0.1"),
             ("level", "-1"), ("level", "4")],
        )  # fmt: skip
        def it_rejects_an_out_of_range_value(self, param: str, value: str):
            with pytest.raises(BadRequest, match=param):
                _ = timeline(**{param: value})

        @pytest.mark.parametrize("value", ["1.5", "two", ""])
        def it_rejects_a_level_that_isnt_a_whole_number(self, value: str):
            with pytest.raises(BadRequest, match="level"):
                _ = timeline(level=value)

        def it_says_the_levels_range(self):
            with pytest.raises(BadRequest, match="from 0 to 3, got 4"):
                _ = timeline(level="4")


def _skip_without_data() -> None:
    root = paths.data_dir()
    for path in (root / "gamedata.json/scripts/heroes.json", root / "gamedata.tsv/heroes.tsv"):
        if not path.exists():
            pytest.skip(f"no local game data at {path}; build it with `redo` at the repo root")


class DescribeRealData:
    def it_runs_the_timeline_for_every_live_hero_and_listed_ability(self):
        _skip_without_data()
        assert load_data() is load_data()
        lines = QUERIES["heroes"].run({})
        assert len(lines) > 10 and all(line["name"] != line["hero"] for line in lines), lines
        heroes = [str(line["hero"]) for line in lines]
        for hero in heroes:
            listed = QUERIES["abilities"].run({"hero": hero})
            assert [line["kind"] for line in listed][:3] == ["gun", "melee", "melee"], (hero, listed)
            for line in listed:
                params: Params = {"hero": hero, "ability": str(line["ability"]), "hp": "1000"}
                assert QUERIES["timeline"].run(params), params

    def it_runs_the_timeline_at_the_last_level(self):
        _skip_without_data()
        for hero in [str(line["hero"]) for line in QUERIES["heroes"].run({})]:
            for line in QUERIES["abilities"].run({"hero": hero}):
                params: Params = {"hero": hero, "ability": str(line["ability"]), "level": "35"}
                assert notes(QUERIES["timeline"].run(params))[1].startswith("Level 35 is 35 boons"), params
