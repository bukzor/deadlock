"""The data and the programs share only `records`, so both rules hold from the AST.

- `records` is vocabulary: frozen keyword-only dataclasses and type aliases,
  whose only methods are `@property` derivations, importing only the stdlib's
  typing modules.
- An experiment module imports only `records` and binds `EXPERIMENT`.
"""

import ast
from pathlib import Path

PACKAGE = Path(__file__).parent
RECORDS_MAY_IMPORT = {"dataclasses", "typing", "collections.abc"}
RECORDS_MODULES = {"records", "bukzor_deadlock_measurements.records"}


def _imported_modules(tree: ast.AST) -> list[str]:
    """Each import's module, relative ones as written (`.records`, `..check`)."""
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom):
            names.append("." * node.level + (node.module or ""))
    return names


def _is_frozen_kw_only_dataclass(decorator: ast.expr) -> bool:
    if not (isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Name)):
        return False
    else:
        flags = {k.arg: k.value for k in decorator.keywords}
        return decorator.func.id == "dataclass" and all(
            isinstance(v := flags.get(f), ast.Constant) and v.value is True
            for f in ("frozen", "kw_only")
        )


def _is_docstring(node: ast.stmt) -> bool:
    return isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)


def _class_violations(cls: ast.ClassDef) -> list[str]:
    found: list[str] = []
    if [_is_frozen_kw_only_dataclass(d) for d in cls.decorator_list] != [True]:
        found.append(f"{cls.name}: not @dataclass(frozen=True, kw_only=True)")
    for node in cls.body:
        if isinstance(node, ast.FunctionDef):
            if [ast.unparse(d) for d in node.decorator_list] != ["property"]:
                found.append(f"{cls.name}.{node.name}: a method, not a @property")
        elif not (isinstance(node, ast.AnnAssign) or _is_docstring(node)):
            found.append(f"{cls.name}: line {node.lineno} is not a field")
    return found


def records_violations(source: str) -> list[str]:
    """Each way `source` breaks the vocabulary rule; empty when it keeps it."""
    tree = ast.parse(source)
    found = [
        f"imports {m}" for m in _imported_modules(tree) if m not in RECORDS_MAY_IMPORT
    ]
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            found += _class_violations(node)
        elif not isinstance(
            node, ast.Import | ast.ImportFrom | ast.TypeAlias
        ) and not _is_docstring(node):
            found.append(f"line {node.lineno}: not a dataclass or type alias")
    return found


def experiment_violations(source: str) -> list[str]:
    """Each way `source` breaks the experiment rule; empty when it keeps it."""
    tree = ast.parse(source)
    found = [
        f"imports {m}"
        for m in _imported_modules(tree)
        if m.lstrip(".") not in RECORDS_MODULES
    ]
    bound = {
        t.id
        for node in tree.body
        if isinstance(node, ast.Assign | ast.AnnAssign)
        for t in (node.targets if isinstance(node, ast.Assign) else [node.target])
        if isinstance(t, ast.Name)
    }
    if "EXPERIMENT" not in bound:
        found.append("binds no EXPERIMENT")
    return found


GOOD_RECORDS = '''\
"""doc"""
from collections.abc import Sequence
from dataclasses import dataclass

type Items = Sequence[str]

@dataclass(frozen=True, kw_only=True)
class Health:
    """doc"""
    max: int
    start: int

    @property
    def half(self) -> int:
        return self.max // 2
'''

GOOD_EXPERIMENT = """\
from ..records import Health
BASE = 1
EXPERIMENT = Health(max=BASE, start=BASE)
"""


class DescribeRecordsViolations:
    def it_allows_dataclasses_aliases_and_properties(self):
        assert records_violations(GOOD_RECORDS) == []

    def it_flags_a_plain_function(self):
        source = GOOD_RECORDS + "\ndef heal(h):\n    return h.max\n"
        assert records_violations(source) == ["line 17: not a dataclass or type alias"]

    def it_flags_a_non_frozen_dataclass(self):
        source = GOOD_RECORDS.replace("frozen=True", "frozen=False")
        assert records_violations(source) == [
            "Health: not @dataclass(frozen=True, kw_only=True)"
        ]

    def it_flags_a_dataclass_that_is_not_kw_only(self):
        source = GOOD_RECORDS.replace(", kw_only=True", "")
        assert records_violations(source) == [
            "Health: not @dataclass(frozen=True, kw_only=True)"
        ]

    def it_flags_a_method_that_is_not_a_property(self):
        source = GOOD_RECORDS.replace("    @property\n", "")
        assert records_violations(source) == ["Health.half: a method, not a @property"]

    def it_flags_a_class_body_line_that_is_not_a_field(self):
        source = GOOD_RECORDS.replace("    start: int\n", "    start = 0\n")
        assert records_violations(source) == ["Health: line 11 is not a field"]

    def it_flags_a_foreign_import(self):
        source = "from bukzor_deadlock_lookup.lookup import Lookup\n"
        assert records_violations(source) == ["imports bukzor_deadlock_lookup.lookup"]


class DescribeExperimentViolations:
    def it_allows_records_imports_and_constants(self):
        assert experiment_violations(GOOD_EXPERIMENT) == []

    def it_flags_importing_check(self):
        source = "from ..check import check\n" + GOOD_EXPERIMENT
        assert experiment_violations(source) == ["imports ..check"]

    def it_flags_a_missing_experiment(self):
        source = GOOD_EXPERIMENT.replace("EXPERIMENT", "OTHER")
        assert experiment_violations(source) == ["binds no EXPERIMENT"]


class DescribePackage:
    def it_keeps_records_to_the_vocabulary(self):
        assert records_violations((PACKAGE / "records.py").read_text()) == []

    def it_keeps_each_experiment_to_records(self):
        modules = sorted((PACKAGE / "experiments").glob("[!_]*.py"))
        assert modules, PACKAGE
        found = {
            p.name: bad
            for p in modules
            if (bad := experiment_violations(p.read_text()))
        }
        assert found == {}, found
