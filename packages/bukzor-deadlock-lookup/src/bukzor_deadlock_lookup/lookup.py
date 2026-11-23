"""Heroes, abilities and items, each found by key or English name within its own kind.

A ``Lookup`` is built from in-memory trees, so tests can pass synthetic data;
``load.load`` builds the real one. An ability is any ``abilities.vdata`` entity
without an ``m_iItemTier``; an item is one with it (``bukzor_deadlock.items``).
Resolution is ``resolve.resolve``: a miss raises ``Unresolved``.
"""

from collections.abc import Collection, Mapping
from dataclasses import dataclass
from functools import cached_property

from bukzor_deadlock import items, loc
from bukzor_deadlock.abilities import TEMPLATE_HERO, bindings
from bukzor_deadlock.types import dig, is_str_mapping

from .entities import Ability, Hero, Item
from .resolve import resolve

NOT_PLAYABLE = frozenset(
    {"hero_targetdummy", "hero_genericperson"}
)  # the training dummy; Generic Person


@dataclass(frozen=True)
class Lookup:
    """The ``heroes.vdata`` and ``abilities.vdata`` trees (see ``bukzor_deadlock.gamedata``), the ``{tier: souls}`` item prices (``bukzor_deadlock.items.prices``), and the localization tokens."""

    heroes: Mapping[str, object]
    abilities: Mapping[str, object]
    prices: Mapping[int, int]
    tokens: Mapping[str, str]

    def hero(self, ref: str) -> Hero:
        """The hero ``ref`` names; ``hero_base``, the template, is not one."""
        keys = [
            k
            for k, v in self.heroes.items()
            if is_str_mapping(v) and k != TEMPLATE_HERO
        ]
        return self._hero(resolve(ref, keys, self._names(keys), "hero"))

    def playable(self) -> list[Hero]:
        """The live heroes (``bukzor_deadlock.abilities.bindings``) that have a name and aren't in ``NOT_PLAYABLE``, by name, then key."""
        live = {hero for hero, _, _ in bindings(self.heroes)} - NOT_PLAYABLE
        found = [hero for hero in map(self._hero, live) if hero.name]
        return sorted(found, key=lambda hero: (hero.name or "", hero.key))

    def ability(self, ref: str, hero: str | None = None) -> Ability:
        """The ability ``ref`` names; with ``hero`` (a key or name), only among that hero's kit.

        Many abilities share a name (every hero's melee is "Melee"), which a hero scopes apart.
        """
        if hero is None:
            keys, kind = self._ability_keys, "ability"
        else:
            owner = self.hero(hero)
            keys, kind = set(owner.kit.values()), f"ability of {owner.key}"
        key = resolve(ref, keys, self._names(keys), kind)
        return Ability(key, loc.look_up(self.tokens, key), self._tree(key))

    def item(self, ref: str) -> Item:
        """The item ``ref`` names; only enabled items answer to a name, but any to its key."""
        enabled = [key for key, item in self._items.items() if not item.disabled]
        return self._items[resolve(ref, self._items, self._names(enabled), "item")]

    def label(self, ability: Ability, prop: str) -> str | None:
        """``prop``'s in-game label; ``None`` when the game has none.

        The label is ``{token}_label``, where the token is the property's
        ``m_strLocTokenOverride`` when it has one, else its key: the game's
        tooltips label a property the same way. ``prop`` need not be one of
        ``ability``'s properties.
        """
        override = dig(ability.properties, prop, "m_strLocTokenOverride")
        token = override if isinstance(override, str) and override else prop
        return self.tokens.get(f"{token}_label") or None

    def _hero(self, key: str) -> Hero:
        tree = self.heroes[key]
        assert is_str_mapping(tree), key
        return Hero(key, loc.look_up(self.tokens, key), tree)

    def _tree(self, key: str) -> Mapping[str, object]:
        tree = self.abilities[key]
        assert is_str_mapping(tree), key
        return tree

    def _names(self, keys: Collection[str]) -> dict[str, str]:
        return {key: name for key in keys if (name := loc.look_up(self.tokens, key))}

    @cached_property
    def _ability_keys(self) -> set[str]:
        return {
            k
            for k, v in self.abilities.items()
            if is_str_mapping(v) and k not in self._items
        }

    @cached_property
    def _items(self) -> dict[str, Item]:
        return {
            row.name: Item(
                row.name,
                loc.look_up(self.tokens, row.name),
                self._tree(row.name),
                row.tier,
                row.cost,
                row.slot,
                row.disabled,
                row.components,
            )
            for row in items.items(self.abilities, self.prices)
        }
