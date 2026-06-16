import pytest

from .abilities import Ability, Bound, abilities, bound, render


def _hero(name: str, *, disabled: bool, signatures: list[str]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = [
        {"file": "scripts/heroes.vdata", "path": f"{name}.m_bDisabled", "value": disabled}
    ]
    for i, ability in enumerate(signatures, 1):
        path = f"{name}.m_mapBoundAbilities.ESlot_Signature_{i}"
        rows.append({"file": "scripts/heroes.vdata", "path": path, "value": ability})
    return rows


def _ability(name: str, *, type: str, cooldown: object, charges: object) -> list[dict[str, object]]:
    base = f"{name}.m_mapAbilityProperties"
    return [
        {"file": "scripts/abilities.vdata", "path": f"{name}.m_eAbilityType", "value": type},
        {"file": "scripts/abilities.vdata", "path": f"{base}.AbilityCooldown.m_strValue", "value": cooldown},
        {"file": "scripts/abilities.vdata", "path": f"{base}.AbilityCharges.m_strValue", "value": charges},
    ]


RECORDS = [
    *_hero("hero_a", disabled=False, signatures=["sig_a1", "sig_a2", "sig_a3", "sig_a4"]),
    *_hero("hero_dev", disabled=True, signatures=["unshipped"]),
    {"file": "scripts/heroes.vdata", "path": "hero_a.m_mapBoundAbilities.ESlot_Weapon_Melee", "value": "ignored"},
    *_ability("sig_a1", type="EAbilityType_Signature", cooldown=28.0, charges="2"),
    *_ability("sig_a2", type="EAbilityType_Signature", cooldown="41", charges="1"),
    *_ability("sig_a3", type="EAbilityType_Signature", cooldown="20 18 16", charges="0"),
    *_ability("sig_a4", type="EAbilityType_Ultimate", cooldown=115.0, charges="0"),
]


class DescribeAbilities:
    def it_parses_type_and_keeps_per_level_cooldown_lists_verbatim(self):
        rows = _ability("z", type="EAbilityType_Signature", cooldown="40 30 20", charges="2")
        assert abilities(rows) == {"z": Ability(type="Signature", cooldown="40 30 20", charges="2")}

    def it_drops_a_trailing_zero_from_a_bare_number(self):
        rows = _ability("z", type="EAbilityType_Ultimate", cooldown=115.0, charges=0)
        assert abilities(rows) == {"z": Ability(type="Ultimate", cooldown="115", charges="0")}

    def it_omits_abilities_missing_any_of_the_three_facts(self):
        partial = [{"file": "scripts/abilities.vdata", "path": "z.m_eAbilityType", "value": "EAbilityType_Signature"}]
        assert abilities(partial) == {}


class DescribeBound:
    def it_joins_live_hero_signatures_skipping_disabled_and_nonsignature_slots(self):
        assert bound(RECORDS) == [
            Bound("hero_a", "Signature_1", "sig_a1", "Signature", "28", "2"),
            Bound("hero_a", "Signature_2", "sig_a2", "Signature", "41", "1"),
            Bound("hero_a", "Signature_3", "sig_a3", "Signature", "20 18 16", "0"),
            Bound("hero_a", "Signature_4", "sig_a4", "Ultimate", "115", "0"),
        ]

    def it_fails_when_a_live_hero_lacks_four_signatures(self):
        records = _hero("hero_b", disabled=False, signatures=["sig_a1"]) + _ability(
            "sig_a1", type="EAbilityType_Signature", cooldown="20", charges="0"
        )
        with pytest.raises(AssertionError, match="hero_b"):
            bound(records)

    def it_fails_when_a_live_signature_binding_is_undefined(self):
        records = _hero("hero_b", disabled=False, signatures=["ghost", "x2", "x3", "x4"]) + [
            *_ability("x2", type="EAbilityType_Signature", cooldown="1", charges="0"),
            *_ability("x3", type="EAbilityType_Signature", cooldown="1", charges="0"),
            *_ability("x4", type="EAbilityType_Signature", cooldown="1", charges="0"),
        ]
        with pytest.raises(AssertionError, match="ghost"):
            bound(records)


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
