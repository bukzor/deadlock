"""Player-facing names from the game's English localization (``bukzor_deadlock.loc``).

An ability's name is its own token. A property's label is ``{token}_label``,
where the token is the property's ``m_strLocTokenOverride`` when it has one,
else its key: the game's tooltips label a property the same way.
"""

from collections.abc import Mapping

from bukzor_deadlock import loc, paths
from bukzor_deadlock.types import dig

FILES = ("citadel_heroes", "citadel_attributes")  # ability names; property labels (both files hold some of each)


def load_tokens() -> dict[str, str]:
    """``FILES``' token tables from the install, merged; a token in two files must agree."""
    root = paths.citadel_dir() / "resource/localization"
    merged: dict[str, str] = {}
    for name in FILES:
        with (root / name / f"{name}_english.txt").open(encoding="utf-8-sig") as file:
            table = loc.tokens(file)
        clashes = sorted(k for k in table.keys() & merged.keys() if table[k] != merged[k])
        assert not clashes, (name, clashes)
        merged |= table
    return merged


def ability_name(tokens: Mapping[str, str], ability: str) -> str:
    """``ability``'s in-game name; else its key."""
    return loc.look_up(tokens, ability) or ability


def property_label(tokens: Mapping[str, str], props: Mapping[str, object], prop: str) -> str | None:
    """``prop``'s in-game label, given its ability's properties ``props``; ``None`` when the game has none."""
    override = dig(props, prop, "m_strLocTokenOverride")
    token = override if isinstance(override, str) and override else prop
    return tokens.get(f"{token}_label") or None
