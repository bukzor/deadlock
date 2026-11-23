"""Against the real ``data/`` tree and the installed game's localization."""

import csv

from bukzor_deadlock import paths

from .load import load, load_tokens


class DescribeLoad:
    def it_finds_tankbuster_by_name(self):
        tankbuster = load().item("Tankbuster")
        assert (tankbuster.key, tankbuster.cost) == ("upgrade_magic_shock", 3200)

    def it_finds_yamatos_crimson_slash(self):
        assert (
            load().ability("Crimson Slash", hero="Yamato").key
            == "citadel_ability_healing_slash"
        )

    def it_finds_crimson_slash_unscoped_too(self):
        assert load().ability("Crimson Slash").key == "citadel_ability_healing_slash"

    def it_reads_once_per_process(self):
        assert load() is load()

    def it_plays_the_heroes_heroes_tsv_lists(self):
        with (paths.data_dir() / "gamedata.tsv/heroes.tsv").open(newline="") as file:
            rows = list(csv.DictReader(file, delimiter="\t", quoting=csv.QUOTE_NONE))
        tsv = {r["hero"] for r in rows if r["disabled"] == "false" and r["name"]} - {
            "hero_targetdummy",
            "hero_genericperson",
        }
        assert {hero.key for hero in load().playable()} == tsv


class DescribeLoadTokens:
    def it_merges_hero_ability_and_item_names(self):
        tokens = load_tokens()
        assert [
            tokens["hero_yamato:n"],
            tokens["citadel_ability_healing_slash"],
            tokens["upgrade_magic_shock"],
        ] == [
            "Yamato",
            "Crimson Slash",
            "Tankbuster",
        ]
