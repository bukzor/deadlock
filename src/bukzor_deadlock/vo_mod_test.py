from .vo_captions import tokens
from .vo_mod import caption, render, substitute

GAME = (
    "﻿"
    '"lang"\r\n{\r\n\t"Language"\t\t"French"\r\n\t"Tokens"\r\n\t{\r\n'
    '\t\t"a_hero_3d"\t\t"Parle en japonais."\r\n'
    '\t\t"b_hero_3d"\t\t"Il dit \\"non\\"."\r\n'
    "\t}\r\n}\r\n"
)


def row(
    lang: str = "ja",
    replacement: str = "奇怪な生き物だ。",
    translation: str = "A bizarre creature.",
    event: str = "a_hero_3d",
) -> dict[str, str]:
    return {
        "event": event,
        "lang": lang,
        "replacement": replacement,
        "translation": translation,
    }


class DescribeCaption:
    def it_brackets_the_translation_on_a_new_line(self):
        assert (
            caption(row(), "english", {}) == "奇怪な生き物だ。<br>[A bizarre creature.]"
        )

    def it_drops_the_bracket_in_the_spoken_language(self):
        assert caption(row(), "japanese", {}) == "奇怪な生き物だ。"
        assert caption(row("es", "Hola."), "latam", {}) == "Hola."

    def it_uses_the_locale_translation(self):
        translations = {("A bizarre creature.", "french"): "Une créature bizarre."}
        assert (
            caption(row(), "french", translations)
            == "奇怪な生き物だ。<br>[Une créature bizarre.]"
        )

    def it_reads_latin_script_under_ja_as_english(self):
        vermin = row(replacement="Vermin.", translation="Vermin!")
        assert caption(vermin, "english", {}) == "Vermin."
        assert caption(vermin, "japanese", {}) == "Vermin.<br>[Vermin!]"

    def it_drops_a_bracket_that_repeats_the_line(self):
        vermin = row(replacement="Vermin.", translation="Vermin.")
        assert caption(vermin, "japanese", {}) == "Vermin."

    def it_reads_auto_as_english(self):
        auto = row("auto", "That furnace is dead!", "Infernus is dead!")
        assert caption(auto, "english", {}) == "That furnace is dead!"
        assert caption(auto, "german", {}) == (
            "That furnace is dead!<br>[Infernus is dead!]"
        )


class DescribeRender:
    def it_round_trips_through_the_caption_reader(self):
        ours = {"a_hero_3d": 'Er sagt "ja" \\ nein.'}
        assert tokens(render(GAME, ours).removeprefix("\ufeff")) == ours

    def it_keeps_the_game_header(self):
        assert render(GAME, {}).startswith(GAME[: GAME.index("\t\t")])


class DescribeSubstitute:
    def it_replaces_in_place_and_keeps_the_rest(self):
        assert substitute(GAME, {"a_hero_3d": "X"}) == GAME.replace(
            "Parle en japonais.", "X"
        )

    def it_appends_a_token_the_game_lacks(self):
        out = substitute(GAME, {"c_hero_3d": "Y"})
        assert out.endswith('\t\t"c_hero_3d"\t\t"Y"\r\n\t}\r\n}\r\n'), out
        assert tokens(out.removeprefix("\ufeff"))["b_hero_3d"] == 'Il dit "non".'

    def it_appends_before_a_brace_indented_twice(self):
        game = GAME.replace("\t}\r\n}", "\t\t}\r\n}")
        out = substitute(game, {"c_hero_3d": "Y"})
        assert out.endswith('"\r\n\t\t"c_hero_3d"\t\t"Y"\r\n\t\t}\r\n}\r\n'), out
