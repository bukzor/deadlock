"""Turn a key or an English name into a key, among one kind's candidates."""

import difflib
from collections.abc import Collection, Mapping

NEAR = 5  # how many near candidates an error names


class Unresolved(LookupError):
    """A reference names no candidate, or more than one; the message says which, and what is near."""


def resolve(
    ref: str, keys: Collection[str], names: Mapping[str, str], kind: str
) -> str:
    """``ref`` if it is one of ``keys``, else the one key whose English name (in ``names``) is ``ref``, ignoring case.

    ``kind`` (``"hero"``, ``"item"``, ...) only words the error. A name whose
    key is not in ``keys`` is never a match: the caller scopes the candidates.
    """
    if ref in keys:
        return ref
    matches = sorted(
        key for key in keys if key in names and names[key].casefold() == ref.casefold()
    )
    if len(matches) == 1:
        return matches[0]
    elif matches:
        raise Unresolved(
            f"ambiguous {kind}: {ref!r} names {', '.join(matches)}: give the key"
        )
    else:
        near = _near(ref, keys, names)
        listed = ", ".join(_label(key, names) for key in near) if near else ""
        raise Unresolved(
            f"unknown {kind}: {ref!r} ({f'near: {listed}' if near else 'nothing near'})"
        )


def _near(ref: str, keys: Collection[str], names: Mapping[str, str]) -> list[str]:
    """The keys whose name or key is most like ``ref``, best first."""
    choices: dict[str, str] = {}  # casefolded name or key: key
    for key in sorted(keys):
        _ = choices.setdefault(key.casefold(), key)
        if key in names:
            _ = choices.setdefault(names[key].casefold(), key)
    close = difflib.get_close_matches(ref.casefold(), choices, n=NEAR * 2)
    return list(dict.fromkeys(choices[choice] for choice in close))[:NEAR]


def _label(key: str, names: Mapping[str, str]) -> str:
    return f"{names[key]} = {key}" if key in names else key
