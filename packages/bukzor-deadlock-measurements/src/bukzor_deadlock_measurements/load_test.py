import copy
from typing import cast

import pytest

from .load import ReadingsError, load_all, parse

DOC: dict[str, object] = {
    "experiment": "x",
    "dummies": [
        {
            "max_health": 1,
            "spirit_resist": 0.1,
            "regen": [1.5],
            "scenarios": [
                {
                    "name": "a",
                    "items": ["I"],
                    "hero": {"spirit": 1, "health": {"max": 2, "start": 1}},
                }
            ],
        }
    ],
}


def dummy(doc: dict[str, object]) -> dict[str, object]:
    return cast(list[dict[str, object]], doc["dummies"])[0]


class DescribeParse:
    def it_builds_records(self):
        e = parse(DOC)
        assert e.dummies[0].scenarios[0].heal is None

    def it_rejects_unknown_keys(self):
        with pytest.raises(ReadingsError, match="Additional properties"):
            _ = parse({**DOC, "extra": 1})

    def it_rejects_missing_keys(self):
        doc = copy.deepcopy(DOC)
        del dummy(doc)["regen"]
        with pytest.raises(ReadingsError, match="required property"):
            _ = parse(doc)

    def it_rejects_wrong_types(self):
        doc = copy.deepcopy(DOC)
        dummy(doc)["max_health"] = "10"
        with pytest.raises(ReadingsError, match="is not of type .integer."):
            _ = parse(doc)


class DescribeShippedData:
    def it_loads_every_file(self):
        (crimson,) = load_all()
        assert crimson.name == "crimson-slash"
        heals = [s.heal for s in crimson.dummies[0].scenarios]
        assert heals == [463, 467, 557, 923]

    def it_names_the_file_and_path_of_a_violation(self):
        doc = copy.deepcopy(DOC)
        dummy(doc)["max_health"] = "10"
        with pytest.raises(ReadingsError, match=r"f\.yaml\.dummies\[0\]\.max_health"):
            _ = parse(doc, "f.yaml")
