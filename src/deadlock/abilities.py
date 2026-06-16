"""Recompile ``abilities.tsv`` — each live hero's four signature abilities — from data.

Source: the committed, flattened ``data/gamedata.jsonl``. Heroes in
``scripts/heroes.vdata`` bind abilities to slots via ``m_mapBoundAbilities``;
the abilities are defined in ``scripts/abilities.vdata``. This table resolves
that join for the four ``ESlot_Signature_*`` slots — the upgradeable, hero-
defining kit.

Scope is the *live* roster (``m_bDisabled`` false). In-development heroes are
excluded because their abilities aren't shipped in ``abilities.vdata`` at all
(or are borrowed placeholders) — emitting them would fabricate rows. The weapon
and movement slots are deliberately omitted: weapons aren't abilities with these
stats, and the movement kit is shared.

One row per (hero, slot), sorted:

- ``ability``  — the bound ability entity name.
- ``type``     — ``m_eAbilityType`` (``EAbilityType_`` stripped); the 4th slot
  is the ``Ultimate``, the rest ``Signature``.
- ``cooldown`` — ``AbilityCooldown`` in seconds; a space-separated list when the
  cooldown scales per upgrade level (e.g. ``40 30 20``).
- ``charges``  — ``AbilityCharges`` (0 = single cast on cooldown).

(``m_iMaxLevel`` and the upgrade-tier count are intentionally absent: both are
constant across every ability, so they carry no information.)

Every live hero must bind four signatures that all resolve and carry these base
stats; that invariant is asserted so a dangling binding on a shipped hero fails
loudly.

    python -m deadlock.abilities data/gamedata.jsonl
"""

from __future__ import annotations

import json
import re
import sys
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

HEROES_FILE = "scripts/heroes.vdata"
ABILITIES_FILE = "scripts/abilities.vdata"
_BOUND = re.compile(r"^(hero_\w+)\.m_mapBoundAbilities\.ESlot_(Signature_\d)$")
_DISABLED = re.compile(r"^(hero_\w+)\.m_bDisabled$")
_PROP = re.compile(
    r"^(\w+)\.(?:m_eAbilityType$|m_mapAbilityProperties\.(AbilityCooldown|AbilityCharges)\.m_strValue$)"
)
SIGNATURE_SLOTS = 4


@dataclass(frozen=True)
class Ability:
    """An ability's joined base facts, keyed by entity name."""

    type: str
    cooldown: str
    charges: str


@dataclass(frozen=True)
class Bound:
    """One emitted ``abilities.tsv`` row: a live hero's signature ability."""

    hero: str
    slot: str
    ability: str
    type: str
    cooldown: str
    charges: str


def abilities(records: Iterable[Mapping[str, object]]) -> dict[str, Ability]:
    """Per-ability ``{type, cooldown, charges}``, parsed from abilities.vdata."""
    raw: dict[str, dict[str, object]] = {}
    for record in records:
        if record["file"] != ABILITIES_FILE:
            continue
        match = _PROP.match(_str(record["path"]))
        if not match:
            continue
        key = match.group(2) or "type"
        raw.setdefault(match.group(1), {})[key] = record["value"]
    return {
        name: Ability(
            type=_str(f["type"]).removeprefix("EAbilityType_"),
            cooldown=_value(f["AbilityCooldown"]),
            charges=_value(f["AbilityCharges"]),
        )
        for name, f in raw.items()
        if {"type", "AbilityCooldown", "AbilityCharges"} <= set(f)
    }


def bindings(records: Iterable[Mapping[str, object]]) -> tuple[dict[str, dict[str, str]], dict[str, bool]]:
    """Per-hero signature ``{slot: ability}`` maps and the ``m_bDisabled`` flag."""
    bound: dict[str, dict[str, str]] = {}
    disabled: dict[str, bool] = {}
    for record in records:
        if record["file"] != HEROES_FILE:
            continue
        path = _str(record["path"])
        slot = _BOUND.match(path)
        if slot:
            bound.setdefault(slot.group(1), {})[slot.group(2)] = _str(record["value"])
        flag = _DISABLED.match(path)
        if flag:
            disabled[flag.group(1)] = _bool(record["value"])
    return bound, disabled


def bound(records: Iterable[Mapping[str, object]]) -> list[Bound]:
    """Live heroes' signature bindings joined to ability stats; assert each resolves."""
    records = list(records)
    defined = abilities(records)
    sigs, disabled = bindings(records)
    result: list[Bound] = []
    for hero, slots in sigs.items():
        if disabled[hero]:
            continue
        assert len(slots) == SIGNATURE_SLOTS, (hero, sorted(slots))
        for slot, ability in slots.items():
            assert ability in defined, (hero, slot, ability)
            stats = defined[ability]
            result.append(Bound(hero, slot, ability, stats.type, stats.cooldown, stats.charges))
    return sorted(result, key=lambda b: (b.hero, b.slot))


def render(bound: Iterable[Bound]) -> str:
    """Render the kit as a tab-separated table with a header line."""
    body = "".join(
        f"{b.hero}\t{b.slot}\t{b.ability}\t{b.type}\t{b.cooldown}\t{b.charges}\n" for b in bound
    )
    return "hero\tslot\tability\ttype\tcooldown\tcharges\n" + body


def _value(value: object) -> str:
    """Render a KV3 ``m_strValue``: a bare number loses a trailing ``.0``; a
    string (possibly a space-separated per-level list) is kept verbatim."""
    if isinstance(value, bool):
        raise AssertionError(value)
    if isinstance(value, (int, float)):
        return str(int(value)) if value == int(value) else str(value)
    return _str(value)


def _str(value: object) -> str:
    assert isinstance(value, str), value
    return value


def _bool(value: object) -> bool:
    assert isinstance(value, bool), value
    return value


def main(argv: list[str]) -> None:
    [source] = argv[1:]
    records = (json.loads(line) for line in Path(source).read_text().splitlines())
    sys.stdout.write(render(bound(records)))


if __name__ == "__main__":
    main(sys.argv)
