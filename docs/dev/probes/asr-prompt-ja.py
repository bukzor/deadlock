"""Print a Japanese proper-noun prompt for whisper from the game's own names.

    python docs/dev/probes/asr-prompt-ja.py "$DEADLOCK_HOME" > prompt.ja.txt

Every hero display name (``hero_<x>:n``) from the loose
``citadel_gc_hero_names_japanese.txt``, then Yamato's four ability names from
``citadel_heroes_japanese.txt``, joined by 「、」.
"""

import re
import sys
from pathlib import Path

LOC = "game/citadel/resource/localization"
ABILITIES = ("power_slash", "flying_strike", "healing_slash", "infinity_slash")


def main(home: Path) -> None:
    names = (
        home / LOC / "citadel_gc_hero_names/citadel_gc_hero_names_japanese.txt"
    ).read_text(encoding="utf-8-sig")
    heroes = sorted(set(re.findall(r'"hero_[a-z0-9]+:n"\s+"([^"]+)"', names)))
    text = (home / LOC / "citadel_heroes/citadel_heroes_japanese.txt").read_text(
        encoding="utf-8-sig"
    )
    abilities = [
        m.group(1)
        for a in ABILITIES
        if (m := re.search(rf'"citadel_ability_{a}"\s+"([^"]+)"', text))
    ]
    print("、".join(heroes + abilities))


if __name__ == "__main__":
    main(Path(sys.argv[1]))
