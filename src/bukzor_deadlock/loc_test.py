import pytest

from .loc import look_up, tokens

LINES = [
    '"lang"\r\n',
    "{\r\n",
    '\t"Language"\t\t"english"\r\n',
    '\t"Tokens"\r\n',
    "\t{\r\n",
    "\t\t// Hero names (tokens match the hero name directly)\r\n",
    '\t\t"hero_astro:n" "Holliday"\r\n',
    '\t\t"hero_astro_search:n" "Holliday"\r\n',
    '\t\t"hero_krill:n" "Mo & Krill"\r\n',
    '\t\t"hero_bare" "Bare"\r\n',
    "\t}\r\n",
    "}\r\n",
]


class DescribeTokens:
    def it_reads_quoted_pairs_ignoring_braces_and_comments(self):
        assert tokens(LINES) == {
            "lang": "",
            "Language": "english",
            "Tokens": "",
            "hero_astro:n": "Holliday",
            "hero_astro_search:n": "Holliday",
            "hero_krill:n": "Mo & Krill",
            "hero_bare": "Bare",
        }

    def it_rejects_a_duplicated_token(self):
        with pytest.raises(AssertionError, match="hero_astro:n"):
            _ = tokens(LINES + ['\t\t"hero_astro:n" "Other"\r\n'])


class DescribeLookUp:
    def it_prefers_the_noun_case_of_a_token(self):
        assert look_up(tokens(LINES), "hero_astro") == "Holliday"

    def it_falls_back_to_the_bare_token(self):
        assert look_up(tokens(LINES), "hero_bare") == "Bare"

    def it_is_none_for_an_untranslated_token(self):
        assert look_up(tokens(LINES), "hero_base") is None
