"""The scanner runs under a bare Windows `python.exe`: its modules import only
the stdlib and `dllscan` itself. Tests run WSL-side only, so they are exempt."""

import ast
import sys
from pathlib import Path

PACKAGE = Path(__file__).parent


def foreign_imports(source: str) -> list[str]:
    """Top-level names of absolute imports outside the stdlib and `dllscan`."""
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names += [alias.name for alias in node.names]
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            names.append(node.module)
    tops = (name.partition(".")[0] for name in names)
    return [top for top in tops if top not in sys.stdlib_module_names | {"dllscan"}]


class DescribeForeignImports:
    def it_flags_a_third_party_import(self):
        assert foreign_imports("import pytest") == ["pytest"]

    def it_flags_a_third_party_from_import(self):
        assert foreign_imports("from pefile import PE") == ["pefile"]

    def it_flags_by_top_level_name(self):
        assert foreign_imports("import deadlock.paths") == ["deadlock"]

    def it_flags_imports_nested_in_functions(self):
        assert foreign_imports("def f():\n    import capstone\n") == ["capstone"]

    def it_allows_stdlib_dllscan_and_relative_imports(self):
        source = "import ctypes, os.path\nfrom dllscan.memory import Memory\nfrom .memory import Read\nfrom . import flags\n"
        assert foreign_imports(source) == []


class DescribeDllscan:
    def it_imports_only_stdlib_and_itself(self):
        modules = sorted(p for p in PACKAGE.glob("*.py") if not p.name.endswith("_test.py"))
        assert modules, PACKAGE
        found = {p.name: bad for p in modules if (bad := foreign_imports(p.read_text()))}
        assert found == {}, found
