import pytest

from .resolve import Unresolved, resolve

KEYS = {
    "upgrade_magic_shock",
    "upgrade_mystic_reverb",
    "upgrade_a",
    "upgrade_b",
    "upgrade_unnamed",
}
NAMES = {
    "upgrade_magic_shock": "Tankbuster",
    "upgrade_mystic_reverb": "Mystic Reverb",
    "upgrade_a": "Twin",
    "upgrade_b": "Twin",
}


class DescribeResolve:
    def it_takes_a_key(self):
        assert resolve("upgrade_unnamed", KEYS, NAMES, "item") == "upgrade_unnamed"

    def it_takes_an_english_name(self):
        assert resolve("Tankbuster", KEYS, NAMES, "item") == "upgrade_magic_shock"

    def it_ignores_case_in_names(self):
        assert resolve("mystic reverb", KEYS, NAMES, "item") == "upgrade_mystic_reverb"

    def it_ignores_a_name_whose_key_is_not_a_candidate(self):
        with pytest.raises(Unresolved):
            _ = resolve("Tankbuster", KEYS - {"upgrade_magic_shock"}, NAMES, "item")

    class WhenUnknown:
        def it_names_the_kind_and_the_near_candidates(self):
            with pytest.raises(Unresolved) as error:
                _ = resolve("Tankbustr", KEYS, NAMES, "item")
            assert (
                str(error.value)
                == "unknown item: 'Tankbustr' (near: Tankbuster = upgrade_magic_shock)"
            )

        def it_says_when_nothing_is_near(self):
            with pytest.raises(Unresolved) as error:
                _ = resolve("zzzz", KEYS, NAMES, "hero")
            assert str(error.value) == "unknown hero: 'zzzz' (nothing near)"

        def it_finds_near_keys_too(self):
            with pytest.raises(Unresolved) as error:
                _ = resolve("upgrade_magic_shok", KEYS, NAMES, "item")
            assert "Tankbuster = upgrade_magic_shock" in str(error.value)

    class WhenAmbiguous:
        def it_names_every_match(self):
            with pytest.raises(Unresolved) as error:
                _ = resolve("Twin", KEYS, NAMES, "item")
            assert (
                str(error.value)
                == "ambiguous item: 'Twin' names upgrade_a, upgrade_b: give the key"
            )
