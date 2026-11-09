import pytest

from .dlls_load_tree import edges, tree

TSV = """\
dll	outcome	detail
Qt5Core.dll	ok	netapi32.dll qt5core.dll shell32.dll
Qt5Gui.dll	ok	d3d11.dll netapi32.dll qt5core.dll qt5gui.dll shell32.dll
client.dll	ok	client.dll tier0.dll winmm.dll
engine2.dll	ok	engine2.dll shell32.dll tier0.dll winmm.dll
helpsystem.dll	excluded	LoadLibrary hangs
tier0.dll	ok	tier0.dll winmm.dll
vfx_dx11.dll	failed	LoadLibraryExW: 126
"""


class DescribeEdges:
    def it_keeps_only_the_loads_no_other_load_in_the_closure_explains(self):
        assert edges({"a": {"b", "c", "d"}, "b": {"c"}}) == {"a": ["b", "d"], "b": ["c"]}

    def it_treats_a_module_without_a_known_closure_as_a_leaf(self):
        assert edges({"a": {"shell32.dll", "x"}}) == {"a": ["shell32.dll", "x"]}

    def it_refuses_a_load_cycle(self):
        with pytest.raises(AssertionError, match="load cycle"):
            _ = edges({"a": {"b"}, "b": {"a"}})


class DescribeTree:
    def it_draws_each_root_with_its_inferred_loads_and_annotates_the_rest(self):
        assert tree(TSV) == """\
Qt5Gui.dll
├── Qt5Core.dll
│   ├── netapi32.dll
│   └── shell32.dll
└── d3d11.dll
client.dll
└── tier0.dll
    └── winmm.dll
engine2.dll
├── shell32.dll
└── tier0.dll (*)
helpsystem.dll  [excluded: LoadLibrary hangs]
vfx_dx11.dll  [failed: LoadLibraryExW: 126]

7 dlls: 1 excluded, 1 failed, 5 ok
"""
