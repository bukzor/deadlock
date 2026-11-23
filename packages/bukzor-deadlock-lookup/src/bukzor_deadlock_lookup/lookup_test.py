import pytest

from .entities import Item
from .lookup import Lookup
from .resolve import Unresolved


def hero(slots: dict[str, str], disabled: bool = False) -> dict[str, object]:
    return {
        "m_bDisabled": disabled,
        "m_mapBoundAbilities": {f"ESlot_{s}": a for s, a in slots.items()},
    }


def item(tier: int, disabled: bool = False) -> dict[str, object]:
    return {
        "m_iItemTier": f"EModTier_{tier}",
        "m_eItemSlotType": "EItemSlotType_Tech",
        "m_bDisabled": disabled,
    }


SHOCK_PROPERTIES = {"m_mapAbilityProperties": {"Damage": {"m_strValue": "40"}}}
KIT = {"Weapon_Primary": "gun_a", "Signature_1": "slash"}
LOOKUP = Lookup(
    heroes={
        "generic_data_type": "CitadelHeroData_t",
        "hero_base": hero({}),
        "hero_a": hero(KIT),
        "hero_b": hero({"Signature_1": "slash_b"}),
        "hero_off": hero(KIT, disabled=True),
        "hero_dev": hero(KIT),  # live, but no name
        "hero_targetdummy": hero(KIT),
    },
    abilities={
        "generic_data_type": "CitadelAbilityVData",
        "gun_a": {},
        "slash": {
            "m_mapAbilityProperties": {
                "Damage": {"m_strValue": "1"},
                "AbilityChannelTime": {"m_strLocTokenOverride": "EscapeDuration"},
            }
        },
        "slash_b": {},
        "upgrade_shock": item(3) | SHOCK_PROPERTIES,
        "upgrade_old": item(4, disabled=True),
        "upgrade_new": item(4),
    },
    prices={0: 0, 1: 800, 2: 1600, 3: 3200, 4: 6400},
    tokens={
        "hero_a:n": "Bravo",
        "hero_b:n": "Alpha",
        "hero_off:n": "Off",
        "hero_targetdummy:n": "Dummy",
        "slash": "Slash",
        "Damage_label": "Damage",
        "EscapeDuration_label": "Escape Duration",
        "slash_b": "Slash",
        "upgrade_shock": "Tankbuster",
        "upgrade_old": "Silencer",
        "upgrade_new": "Silencer",
    },
)


class DescribeLookup:
    class WhenFindingAHero:
        def it_takes_a_key_or_a_name(self):
            assert [LOOKUP.hero("hero_a").name, LOOKUP.hero("Alpha").key] == [
                "Bravo",
                "hero_b",
            ]

        def it_never_takes_a_name_of_another_kind(self):
            with pytest.raises(Unresolved, match="unknown hero: 'Tankbuster'"):
                _ = LOOKUP.hero("Tankbuster")

        def it_rejects_a_non_entity_key(self):
            with pytest.raises(Unresolved):
                _ = LOOKUP.hero("generic_data_type")

        def it_rejects_the_template(self):
            with pytest.raises(Unresolved):
                _ = LOOKUP.hero("hero_base")

    class WhenListingPlayableHeroes:
        def it_lists_live_named_heroes_by_name(self):
            assert [h.key for h in LOOKUP.playable()] == ["hero_b", "hero_a"]

    class WhenFindingAnAbility:
        def it_takes_a_key_or_a_name(self):
            assert LOOKUP.ability("gun_a").name is None

        def it_raises_on_a_name_two_abilities_share(self):
            with pytest.raises(
                Unresolved, match="ambiguous ability: 'Slash' names slash, slash_b"
            ):
                _ = LOOKUP.ability("Slash")

        def it_resolves_within_a_heros_kit(self):
            assert LOOKUP.ability("Slash", hero="Alpha").key == "slash_b"

        def it_rejects_an_ability_outside_the_kit(self):
            with pytest.raises(Unresolved, match="unknown ability of hero_b"):
                _ = LOOKUP.ability("gun_a", hero="hero_b")

        def it_never_takes_an_item(self):
            with pytest.raises(Unresolved):
                _ = LOOKUP.ability("upgrade_shock")

    class WhenLabelingAProperty:
        def it_is_the_in_game_label(self):
            assert LOOKUP.label(LOOKUP.ability("slash_b"), "Damage") == "Damage"

        def it_follows_the_propertys_token_override(self):
            slash = LOOKUP.ability("slash")
            assert LOOKUP.label(slash, "AbilityChannelTime") == "Escape Duration"

        def it_is_none_when_the_game_has_no_label(self):
            assert LOOKUP.label(LOOKUP.ability("slash"), "BrewEffectiveness") is None

    class WhenFindingAnItem:
        def it_takes_a_name_with_its_tier_cost_and_slot(self):
            assert LOOKUP.item("Tankbuster") == Item(
                key="upgrade_shock",
                name="Tankbuster",
                tier=3,
                cost=3200,
                slot="Tech",
                disabled=False,
                components=(),
                tree=item(3) | SHOCK_PROPERTIES,
            )

        def it_reads_its_properties_as_an_ability_does(self):
            assert LOOKUP.item("Tankbuster").value("Damage") == 40.0

        def it_names_only_enabled_items(self):
            assert LOOKUP.item("Silencer").key == "upgrade_new"

        def it_still_takes_a_disabled_items_key(self):
            assert LOOKUP.item("upgrade_old").disabled

        def it_never_takes_an_ability(self):
            with pytest.raises(Unresolved):
                _ = LOOKUP.item("slash")
