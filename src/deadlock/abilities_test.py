import pytest

from .abilities import Ability, Bound, abilities, bound, render


def _hero(*, disabled: bool, signatures: list[str], extra_slots: dict[str, str] | None = None) -> dict[str, object]:
    slots = {f"ESlot_Signature_{i}": ability for i, ability in enumerate(signatures, 1)} | (extra_slots or {})
    return {"m_bDisabled": disabled, "m_mapBoundAbilities": slots}


def _ability(*, type: str, cooldown: object, charges: object) -> dict[str, object]:
    return {
        "m_eAbilityType": type,
        "m_mapAbilityProperties": {
            "AbilityCooldown": {"m_strValue": cooldown},
            "AbilityCharges": {"m_strValue": charges},
        },
    }


HEROES = {
    "hero_a": _hero(
        disabled=False,
        signatures=["sig_a1", "sig_a2", "sig_a3", "sig_a4"],
        extra_slots={"ESlot_Weapon_Melee": "ignored"},
    ),
    "hero_dev": _hero(disabled=True, signatures=["unshipped"]),
    "_include": ["scripts/other.vdata"],
}
ABILITIES = {
    "sig_a1": _ability(type="EAbilityType_Signature", cooldown=28.0, charges="2"),
    "sig_a2": _ability(type="EAbilityType_Signature", cooldown="41", charges="1"),
    "sig_a3": _ability(type="EAbilityType_Signature", cooldown="20 18 16", charges="0"),
    "sig_a4": _ability(type="EAbilityType_Ultimate", cooldown=115.0, charges="0"),
}


class DescribeAbilities:
    def it_parses_type_and_keeps_per_level_cooldown_lists_verbatim(self):
        rows = {"z": _ability(type="EAbilityType_Signature", cooldown="40 30 20", charges="2")}
        assert abilities(rows) == {"z": Ability(type="Signature", cooldown="40 30 20", charges="2")}

    def it_drops_a_trailing_zero_from_a_bare_number(self):
        rows = {"z": _ability(type="EAbilityType_Ultimate", cooldown=115.0, charges=0)}
        assert abilities(rows) == {"z": Ability(type="Ultimate", cooldown="115", charges="0")}

    def it_omits_abilities_missing_any_of_the_three_facts(self):
        partial = {"z": {"m_eAbilityType": "EAbilityType_Signature"}, "_include": ["x"]}
        assert abilities(partial) == {}


class DescribeBound:
    def it_joins_live_hero_signatures_skipping_disabled_and_nonsignature_slots(self):
        assert bound(HEROES, ABILITIES) == [
            Bound("hero_a", "Signature_1", "sig_a1", "Signature", "28", "2"),
            Bound("hero_a", "Signature_2", "sig_a2", "Signature", "41", "1"),
            Bound("hero_a", "Signature_3", "sig_a3", "Signature", "20 18 16", "0"),
            Bound("hero_a", "Signature_4", "sig_a4", "Ultimate", "115", "0"),
        ]

    def it_fails_when_a_live_hero_lacks_four_signatures(self):
        heroes = {"hero_b": _hero(disabled=False, signatures=["sig_a1"])}
        defs = {"sig_a1": _ability(type="EAbilityType_Signature", cooldown="20", charges="0")}
        with pytest.raises(AssertionError, match="hero_b"):
            _ = bound(heroes, defs)

    def it_fails_when_a_live_signature_binding_is_undefined(self):
        heroes = {"hero_b": _hero(disabled=False, signatures=["ghost", "x2", "x3", "x4"])}
        defs = {x: _ability(type="EAbilityType_Signature", cooldown="1", charges="0") for x in ("x2", "x3", "x4")}
        with pytest.raises(AssertionError, match="ghost"):
            _ = bound(heroes, defs)


class DescribeRender:
    def it_emits_a_tab_separated_row_per_ability_with_header(self):
        rows = [
            Bound("hero_a", "Signature_1", "sig_a1", "Signature", "28", "2"),
            Bound("hero_a", "Signature_4", "sig_a4", "Ultimate", "0.6", "0"),
        ]
        assert render(rows) == (
            "hero\tslot\tability\ttype\tcooldown\tcharges\n"
            "hero_a\tSignature_1\tsig_a1\tSignature\t28\t2\n"
            "hero_a\tSignature_4\tsig_a4\tUltimate\t0.6\t0\n"
        )
