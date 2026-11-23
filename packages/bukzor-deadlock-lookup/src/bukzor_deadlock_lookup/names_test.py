import pytest
from bukzor_deadlock import paths

from . import names

TOKENS = {"ability_x:n": "Napalm", "Damage_label": "Damage", "EscapeDuration_label": "Escape Duration", "ability_blank": ""}


class DescribeAbilityName:
    def it_is_the_in_game_name(self):
        assert names.ability_name(TOKENS, "ability_x") == "Napalm"

    @pytest.mark.parametrize("key", ["ability_y", "ability_blank"])
    def it_falls_back_to_the_key(self, key: str):
        assert names.ability_name(TOKENS, key) == key


class DescribePropertyLabel:
    def it_is_the_in_game_label(self):
        assert names.property_label(TOKENS, {"Damage": {"m_strValue": "1"}}, "Damage") == "Damage"

    def it_follows_the_propertys_token_override(self):
        props = {"AbilityChannelTime": {"m_strLocTokenOverride": "EscapeDuration"}}
        assert names.property_label(TOKENS, props, "AbilityChannelTime") == "Escape Duration"

    def it_labels_a_property_the_ability_does_not_list(self):
        assert names.property_label(TOKENS, {}, "Damage") == "Damage"

    def it_is_none_when_the_game_has_no_label(self):
        assert names.property_label(TOKENS, {}, "BrewEffectiveness") is None


class DescribeLoadTokens:
    def it_reads_the_installs_ability_names_and_property_labels(self):
        if not paths.citadel_dir().exists():
            pytest.skip(f"no game install at {paths.citadel_dir()}")
        tokens = names.load_tokens()
        assert names.ability_name(tokens, "ability_incendiary_projectile") == "Napalm"
        assert names.property_label(tokens, {}, "AbilityCooldown") == "Cooldown"
