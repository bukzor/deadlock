"""Print every vis query's answer at default parameters, for a before/after diff.

Usage, from ``apps/vis/server``: ``uv run python PATH/golden.py > OUT``.
Covers ``heroes``, then ``abilities`` and ``timeline`` for every listed hero
and every ability it lists, plus each at level 10 with 50 spirit, 20 m and
2000 HP. Status and lines are both printed, so an error that moves is a diff.
"""

import json

from vis_server.http import answer, jsonl
from vis_server.queries import QUERIES

VARIED = {"level": "10", "spirit": "50", "distance": "20", "hp": "2000"}


def ask(name: str, params: dict[str, str]) -> str:
    status, lines = answer(QUERIES, name, params.items())
    return f"# {name} {json.dumps(params, sort_keys=True)} -> {status}\n{jsonl(lines)}"


def main():
    print(ask("heroes", {}), end="")
    _, heroes = answer(QUERIES, "heroes", [])
    for h in heroes:
        hero = str(h["hero"])
        print(ask("abilities", {"hero": hero}), end="")
        _, kit = answer(QUERIES, "abilities", [("hero", hero)])
        for a in kit:
            base = {"hero": hero, "ability": str(a["ability"])}
            print(ask("timeline", base), end="")
            print(ask("timeline", base | VARIED), end="")


if __name__ == "__main__":
    main()
