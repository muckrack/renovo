from unittest.mock import patch

import pytest
from renovo import HotModuleReplacement


@pytest.fixture
def hmr():
    hmr = HotModuleReplacement()
    hmr.dependency_graph.add_dependency("module.a", "module.b")
    hmr.dependency_graph.add_dependency("module.b", "module.c")
    hmr.dependency_graph.add_dependency("module.c", "module.d")
    hmr.dependency_graph.add_dependency("module.c", "module.e")
    hmr.dependency_graph.add_dependency("module.c", "module.f")
    hmr.dependency_graph.add_dependency("module.e", "module.d")
    hmr.dependency_graph.add_dependency("module.f", "module.d")
    hmr.dependency_graph.add_dependency("module.g", "module.c")
    hmr.dependency_graph.add_dependency("module.d", "module.b")
    hmr.dependency_graph.add_dependency("module.b", "module.d")
    return hmr


def test_cyclic_dependency_handling(hmr):
    """Test case where HotModuleReplacement handles cyclic dependencies."""
    with patch.object(hmr, "_reload_single_module", return_value=0.0):
        try:
            hmr.reload_module("module.d")
        except RecursionError:
            pytest.fail("RecursionError raised when reloading module")
