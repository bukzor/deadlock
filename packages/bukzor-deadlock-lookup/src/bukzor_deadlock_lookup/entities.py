"""Heroes, abilities and items: a key, an English name, and typed reads of the raw tree.

``tree`` is the entity's own subtree of ``heroes.vdata`` or ``abilities.vdata``
(see ``bukzor_deadlock.gamedata``), kept whole so a reader this module lacks
can still ``dig`` it. ``name`` is ``None`` when the localization has none.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass

from bukzor_deadlock.types import dig, is_sequence, is_str_mapping

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


def _optional(value: object) -> float | None:
    return None if value is None else number(value)


@dataclass(frozen=True)
class Scale:
    """How a property grows with a stat: ``factor`` per point of ``stat`` (``None`` when the data names none)."""

    stat: str | None
    factor: float

    @property
    def spirit(self) -> bool:
        return self.stat == SPIRIT


@dataclass(frozen=True)
class Bonus:
    """What one ability upgrade tier does to one property (an ``m_vecPropertyUpgrades`` entry).

    ``kind`` is its ``m_eUpgradeType``: ``EAddToBase`` (when absent),
    ``EAddToScale``, ``EMultiplyBase`` or ``EMultiplyScale``. ``stat`` is its
    ``m_eScaleStatFilter``, the stat whose scale a ``*Scale`` kind changes.
    """

    amount: float
    kind: str
    stat: str | None


@dataclass(frozen=True)
class Attack:
    """One ``m_mapAttacks`` entry of a melee ability: seconds until the next swing."""

    on_hit: float
    on_miss: float


@dataclass(frozen=True)
class Weapon:
    """The fields of one ``m_mapWeaponInfos`` profile that ``bukzor_deadlock.ability_profiles`` doesn't read; speeds and ranges in engine units (inches)."""

    ammo_per_shot: float
    reload_single: bool  # reloads one bullet at a time
    reload_single_delay: float  # seconds before the first bullet goes in
    bullet_speed: float | None  # ``m_flBulletSpeed``, per second
    speed_curve: tuple[float, ...] | None  # ``m_BulletSpeedCurve``'s speeds, per second
    falloff_start: float | None


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

    def text(self, prop: str) -> str:
        """``prop``'s ``m_strValue`` as the data writes it."""
        assert prop in self.properties, (self.key, prop)
        return str(dig(self.properties, prop, "m_strValue"))

    def weapon(self, profile: str) -> Weapon:
        """The ``m_mapWeaponInfos`` profile ``profile``; an absent field takes the engine's default."""
        stats = dig(self.tree, "m_mapWeaponInfos", profile)
        assert is_str_mapping(stats), (self.key, profile)
        spline = dig(stats, "m_BulletSpeedCurve", "m_spline")
        assert spline is None or is_sequence(spline), (self.key, spline)
        return Weapon(
            ammo_per_shot=number(stats.get("m_iAmmoConsumedPerShot", 1)),
            reload_single=stats.get("m_bReloadSingleBullets") is True,
            reload_single_delay=number(
                stats.get("m_flReloadSingleBulletsInitialDelay", 0)
            ),
            bullet_speed=_optional(stats.get("m_flBulletSpeed")),
            speed_curve=(
                None
                if spline is None
                else tuple(number(dig(point, "y")) for point in spline)
            ),
            falloff_start=_optional(stats.get("m_flDamageFalloffStartRange")),
        )

    def attack(self, kind: str) -> Attack:
        """The ``m_mapAttacks`` entry ``kind`` (``EAttackType_Light``, ...)."""
        attack = dig(self.tree, "m_mapAttacks", kind)
        return Attack(
            on_hit=number(dig(attack, "m_flCooldownOnHit")),
            on_miss=number(dig(attack, "m_flCooldownOnMiss")),
        )

    def bonus(self, tier: int, prop: str) -> Bonus:
        """What upgrade ``tier`` (1..3, ``m_vecAbilityUpgrades``' index + 1) does to ``prop``; ``KeyError`` when nothing.

        A bonus that is not a plain number raises ``NotANumber``, naming the ability, tier and property.
        """
        tiers = self.tree.get("m_vecAbilityUpgrades", ())
        assert is_sequence(tiers), (self.key, tiers)
        entries = (
            dig(tiers[tier - 1], "m_vecPropertyUpgrades")
            if 1 <= tier <= len(tiers)
            else ()
        )
        assert entries is None or is_sequence(entries), (self.key, tier, entries)
        for entry in entries or ():
            if dig(entry, "m_strPropertyName") == prop:
                raw = dig(entry, "m_strBonus")
                kind = dig(entry, "m_eUpgradeType") or "EAddToBase"
                stat = dig(entry, "m_eScaleStatFilter")
                assert isinstance(kind, str) and (stat is None or isinstance(stat, str))
                try:
                    return Bonus(number(raw), kind, stat)
                except NotANumber:
                    raise NotANumber(
                        f"{self.key}: tier {tier}'s {prop} bonus is {raw!r}, not a number"
                    ) from None
        raise KeyError(f"{self.key}: tier {tier} leaves {prop} alone")

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

    def scaling(self, stat: str) -> Scale | None:
        """How ``stat`` grows (``m_mapScalingStats``); ``None`` when it doesn't."""
        scaling = dig(self.tree, "m_mapScalingStats", stat)
        if scaling is None:
            return None
        by = dig(scaling, "eScalingStat")
        assert isinstance(by, str), (self.key, stat, by)
        return Scale(stat=by, factor=number(dig(scaling, "flScale")))

    def per_boon(self, name: str) -> float:
        """What one boon adds to ``name`` (``m_mapStandardLevelUpUpgrades``)."""
        return number(dig(self.tree, "m_mapStandardLevelUpUpgrades", name))

    def grants_boon(self, game_level: int) -> bool:
        """Whether reaching ``game_level`` grants a boon (``m_bUseStandardUpgrade``)."""
        info = dig(self.tree, "m_mapLevelInfo", str(game_level))
        return dig(info, "m_bUseStandardUpgrade") is True


@dataclass(frozen=True)
class Item(Ability):
    """A shop item: an ``abilities.vdata`` entity, read as an ``Ability`` is, with ``bukzor_deadlock.items.Item``'s columns."""

    tier: int
    cost: int  # souls
    slot: str  # Weapon | Armor | Tech | ...
    disabled: bool
    components: tuple[str, ...]  # the items it upgrades from
