"""Heroes, abilities and items: a key, an English name, and typed reads of the raw tree.

``tree`` is the entity's own subtree of ``heroes.vdata`` or ``abilities.vdata``
(see ``bukzor_deadlock.gamedata``), kept whole so a reader this module lacks
can still ``dig`` it. ``name`` is ``None`` when the localization has none.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass

from bukzor_deadlock.types import dig, is_str_mapping

SPIRIT = "ETechPower"
_SPIRIT_CLASS = "scale_function_tech_damage"  # scales with spirit when it names no stat
_NUMBER = re.compile(r"-?(\d+\.?\d*|\.\d+)")
_SLOT_PREFIX = "ESlot_"


class NotANumber(ValueError):
    """A field meant as a number isn't a plain one (``"0.1m"``, a per-level list like ``"40 30 20"``)."""


def number(value: object) -> float:
    """``value`` as a float: an int or float (never a bool), or a string that is exactly a decimal number.

    >>> number("-.5")
    -0.5
    """
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    elif isinstance(value, str) and _NUMBER.fullmatch(value):
        return float(value)
    else:
        raise NotANumber(repr(value))


@dataclass(frozen=True)
class Scale:
    """How a property grows with a stat: ``factor`` per point of ``stat`` (``None`` when the data names none)."""

    stat: str | None
    factor: float

    @property
    def spirit(self) -> bool:
        return self.stat == SPIRIT


@dataclass(frozen=True)
class Ability:
    """An ``abilities.vdata`` entity; ``value``, ``scale`` and ``damage_properties`` read its ``m_mapAbilityProperties``."""

    key: str
    name: str | None
    tree: Mapping[str, object]

    @property
    def properties(self) -> Mapping[str, object]:
        props = self.tree.get("m_mapAbilityProperties", {})
        assert is_str_mapping(props), (self.key, props)
        return props

    def value(self, prop: str, default: float | None = None) -> float:
        """``prop``'s ``m_strValue`` as a number; ``default`` when absent, else ``KeyError``.

        A value that is not a plain number raises ``NotANumber``, naming the ability and property.
        """
        if prop not in self.properties:
            if default is None:
                raise KeyError(f"{self.key}: no property {prop}")
            return default
        raw = dig(self.properties, prop, "m_strValue")
        try:
            return number(raw)
        except NotANumber:
            raise NotANumber(f"{self.key}: {prop} is {raw!r}, not a number") from None

    def scale(self, prop: str) -> Scale | None:
        """``prop``'s ``m_subclassScaleFunction``; ``None`` without one.

        A ``scale_function_tech_damage`` that names no stat scales with spirit (``SPIRIT``).
        """
        function = dig(self.properties, prop, "m_subclassScaleFunction")
        factor = dig(function, "m_flStatScale")
        if factor is None:
            return None
        stat = dig(function, "m_eSpecificStatScaleType")
        assert stat is None or isinstance(stat, str), (self.key, prop, stat)
        if stat is None and dig(function, "_class") == _SPIRIT_CLASS:
            stat = SPIRIT
        return Scale(stat=stat, factor=number(factor))

    def damage_properties(self) -> list[str]:
        """The properties flagged ``m_bIsAbilityDamageProperty``, in the data's order."""
        return [
            prop
            for prop in self.properties
            if dig(self.properties, prop, "m_bIsAbilityDamageProperty") is True
        ]


@dataclass(frozen=True)
class Hero:
    """A ``heroes.vdata`` entity."""

    key: str
    name: str | None
    tree: Mapping[str, object]

    @property
    def kit(self) -> Mapping[str, str]:
        """``{slot: ability key}`` from ``m_mapBoundAbilities``, ``ESlot_`` stripped."""
        bound = self.tree.get("m_mapBoundAbilities", {})
        assert is_str_mapping(bound), (self.key, bound)
        kit: dict[str, str] = {}
        for slot, ability in bound.items():
            assert isinstance(ability, str), (self.key, slot, ability)
            kit[slot.removeprefix(_SLOT_PREFIX)] = ability
        return kit

    def stat(self, name: str) -> float:
        """One ``m_mapStartingStats`` entry; every hero carries every stat (see ``bukzor_deadlock.heroes``)."""
        value = dig(self.tree, "m_mapStartingStats", name)
        assert value is not None, (self.key, name)
        return number(value)


@dataclass(frozen=True)
class Item:
    """A shop item: ``bukzor_deadlock.items.Item``'s columns, with its English name."""

    key: str
    name: str | None
    tier: int
    cost: int  # souls
    slot: str  # Weapon | Armor | Tech | ...
    disabled: bool
    components: tuple[str, ...]  # the items it upgrades from
