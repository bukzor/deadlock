"""Collect the experiments: every module in `experiments/` binds its `SETUPS`."""

import importlib
import pkgutil
from typing import cast

from . import experiments
from .records import ExperimentalSetup

type Experiments = dict[str, tuple[ExperimentalSetup, ...]]


def load_all() -> Experiments:
    """Each experiment module's `SETUPS`, by module name, in name order."""
    found: Experiments = {}
    for module in sorted(m.name for m in pkgutil.iter_modules(experiments.__path__)):
        namespace = vars(importlib.import_module(f"{experiments.__name__}.{module}"))
        setups = cast(tuple[object, ...], namespace["SETUPS"])
        assert all(isinstance(s, ExperimentalSetup) for s in setups), module
        found[module] = cast(tuple[ExperimentalSetup, ...], setups)
    return found
