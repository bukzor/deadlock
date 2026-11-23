"""Collect the experiments: every module in `experiments/` binds one `EXPERIMENT`."""

import importlib
import pkgutil
from typing import cast

from . import experiments
from .records import Experiment


def load_all() -> tuple[Experiment, ...]:
    """Each experiment module's `EXPERIMENT`, in module-name order."""
    found: list[Experiment] = []
    for module in sorted(m.name for m in pkgutil.iter_modules(experiments.__path__)):
        namespace = vars(importlib.import_module(f"{experiments.__name__}.{module}"))
        experiment = cast(object, namespace["EXPERIMENT"])
        assert isinstance(experiment, Experiment), (module, experiment)
        found.append(experiment)
    return tuple(found)
