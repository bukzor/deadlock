from collections.abc import Mapping, Sequence

import pytest
from deadlock import paths
from pytest import approx

from .queries import QUERIES, GameData, load_data, registry
from .types import BadRequest, JsonObj, Params

TECH = {"_class": "scale_function_tech_damage", "m_flStatScale": 0.5, "m_eSpecificStatScaleType": "ETechPower"}


def _props(**values: object) -> dict[str, object]:
    return {k: v if isinstance(v, Mapping) else {"m_strValue": v} for k, v in values.items()}


def _hero(slots: Mapping[str, str], disabled: bool = False) -> dict[str, object]:
    return {
        "m_bDisabled": disabled,
        "m_mapStartingStats": {"ELightMeleeDamage": 50, "EHeavyMeleeDamage": 116},
        "m_mapBoundAbilities": {f"ESlot_{slot}": ability for slot, ability in slots.items()},
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
    },
    abilities={
        "gun_a": {"m_mapWeaponInfos": {"primary": GUN}},
        "melee_a": {"m_mapAttacks": {"EAttackType_Light": ATTACK, "EAttackType_Heavy": ATTACK}},
        "blast": {"m_mapAbilityProperties": _props(Damage={"m_strValue": "100", "m_subclassScaleFunction": TECH},
                                                   AbilityCooldown="10", AbilityCastDelay="0.5")},
        "buff": {"m_mapAbilityProperties": _props(AbilityCooldown="20")},
    },  # fmt: skip
    names={"hero_a": "Alpha", "hero_c": "Charlie", "hero_off": "Off"},
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
            "timeline": {"hero", "ability", "horizon", "distance", "spirit", "windup", "hp"},
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
    def it_lists_each_live_hero_by_key_with_its_display_name(self):
        assert run("heroes") == [{"hero": "hero_a", "name": "Alpha"}, {"hero": "hero_c", "name": "Charlie"}]


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


class DescribeTimeline:
    def it_emits_hits_then_measures_then_notes(self):
        found = [str(line["kind"]) for line in timeline()]
        assert found == sorted(found, key=["hit", "measure", "note"].index), found
        assert set(found) == {"hit", "measure", "note"}

    def it_emits_each_unrolled_hit(self):
        assert kinds(timeline(horizon="1", windup="0.25"), "hit") == [
            {"kind": "hit", "trigger": 0.0, "land": 0.25, "damage": 50.0, "label": "light melee", "cycle": 0},
            {"kind": "hit", "trigger": 0.75, "land": 1.0, "damage": 50.0, "label": "light melee", "cycle": 1},
        ]

    def it_unrolls_10_seconds_by_default(self):
        assert max(float(str(h["trigger"])) for h in kinds(timeline(), "hit")) == 9.75

    def it_emits_each_measure(self):
        measures = kinds(timeline(horizon="1"), "measure")
        assert [m["name"] for m in measures] == ["uptime_dps", "steady_dps", "total_damage", "average_dps", "first_land"]
        assert measures[1] == {
            "kind": "measure", "name": "steady_dps", "value": approx(50 / 0.75), "unit": "damage/s",
            "check": measures[1]["check"],
        }  # fmt: skip
        assert all(set(m) == {"kind", "name", "value", "unit", "check"} and m["check"] for m in measures)

    def it_notes_the_sources_caveats_and_level_zero(self):
        found = notes(timeline(windup="0.3"))
        assert any("windup" in n for n in found), found
        assert found[-1] == "Stats are level 0, with no items.", found

    @pytest.mark.parametrize(
        ("ability", "param", "value", "field", "expected"),
        [
            ("gun_a", "distance", "50", "land", 0.005),
            ("melee_heavy", "windup", "0.4", "land", 0.4),
            ("blast", "spirit", "10", "damage", 105),
        ],
    )
    def it_passes_each_parameter_to_its_source(self, ability: str, param: str, value: str, field: str, expected: float):
        assert kinds(timeline(ability, **{param: value}), "hit")[0][field] == approx(expected)

    class WhenGivenHp:
        def it_measures_time_to_kill(self):
            measures = {m["name"]: m["value"] for m in kinds(timeline(hp="100", windup="0.25"), "measure")}
            assert measures["time_to_kill"] == 1.0

        def it_notes_hp_not_reached_within_the_horizon(self):
            lines = timeline(hp="101", horizon="1")
            assert "time_to_kill" not in [m["name"] for m in kinds(lines, "measure")]
            assert any("101" in n and "1 s" in n for n in notes(lines)), notes(lines)

        def it_says_nothing_of_hp_when_reached(self):
            assert not any("hp" in n for n in notes(timeline(hp="100", windup="0.25")))

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
            [("horizon", "0"), ("horizon", "-1"), ("hp", "0"), ("distance", "-1"), ("spirit", "-1"), ("windup", "-0.1")],
        )
        def it_rejects_an_out_of_range_value(self, param: str, value: str):
            with pytest.raises(BadRequest, match=param):
                _ = timeline(**{param: value})


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
