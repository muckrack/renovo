import os
import sys
import tempfile

import pytest
from renovo import HotModuleReplacement

reloader = HotModuleReplacement(excludes=["tests.test_loader"])


@pytest.fixture(autouse=True)
def cleanup_modules():
    module_names = ["a", "b", "c", "d"]
    yield
    for module_name in module_names:
        if module_name in sys.modules:
            del sys.modules[module_name]


def update_module(module_name, new_code):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
        temp_file.write(new_code.encode())
        temp_file_path = temp_file.name

    original_module_path = os.path.join(os.path.dirname(__file__), f"{module_name}.py")
    os.rename(original_module_path, original_module_path + ".bak")
    os.rename(temp_file_path, original_module_path)

    try:
        reloader.reload_module(module_name)
    finally:
        os.rename(original_module_path, temp_file_path)
        os.rename(original_module_path + ".bak", original_module_path)
        os.remove(temp_file_path)


def test_initial_import():
    import a

    assert hasattr(a, "func_a")
    assert hasattr(a, "A")
    assert callable(a.func_a)
    assert callable(a.A().do_something)
    assert a.A().do_something() == "A did something"


def test_reload_on_change():
    import a

    a.func_a()
    assert a.A().do_something() == "A did something"
    reloader.reload_module("a")
    assert hasattr(a, "func_a")
    assert hasattr(a, "A")
    assert callable(a.func_a)
    assert callable(a.A().do_something)
    assert a.A().do_something() == "A did something"


def test_dependency_reload():
    import a
    import b
    import c

    c.a = None  # pyright: ignore [reportAttributeAccessIssue]
    a.func_a()
    assert a.A().do_something() == "A did something"
    b.func_b()
    b.B().func_b()
    c.func_c()
    c.C().func_c()

    reloader.reload_module("c")
    assert hasattr(a, "func_a")
    assert hasattr(a, "A")
    assert callable(a.func_a)
    assert callable(a.A().do_something)
    assert a.A().do_something() == "A did something"
    assert hasattr(b, "func_b")
    assert hasattr(b, "B")
    assert callable(b.func_b)
    assert callable(b.B().func_b)
    assert hasattr(c, "func_c")
    assert hasattr(c, "C")
    assert callable(c.func_c)
    assert callable(c.C().func_c)


def test_circular_dependency():
    # Simulate circular dependency
    import a
    import c

    c.a = a  # pyright: ignore [reportAttributeAccessIssue]
    a.func_a()
    assert a.A().do_something() == "A did something"
    c.func_c()
    c.C().func_c()
    assert hasattr(a, "func_a")
    assert hasattr(a, "A")
    assert callable(a.func_a)
    assert callable(a.A().do_something)
    assert hasattr(c, "func_c")
    assert hasattr(c, "C")
    assert callable(c.func_c)
    assert callable(c.C().func_c)

    reloader.reload_module("c")
    assert hasattr(a, "func_a")
    assert hasattr(a, "A")
    assert callable(a.func_a)
    assert callable(a.A().do_something)
    assert a.A().do_something() == "A did something"
    assert hasattr(c, "func_c")
    assert hasattr(c, "C")
    assert callable(c.func_c)
    assert callable(c.C().func_c)


def test_update_module_a():
    import a

    assert a.A().do_something() == "A did something"  # Initial state

    new_code = """
def func_a():
    print("Updated Function A")

class A:
    def do_something(self):
        print("Updated A method")
        return "A did something updated"
"""
    update_module("a", new_code)

    assert hasattr(a, "func_a")
    assert hasattr(a, "A")
    assert callable(a.func_a)
    assert callable(a.A().do_something)
    a.func_a()
    assert a.A().do_something() == "A did something updated"  # Updated state


def test_update_module_c():
    import a
    import c

    assert c.C().func_c() == "C did something"  # Initial state

    new_code = """
def func_c():
    print("Updated Function C")

class C:
    def func_c(self):
        return "C did something updated"
"""
    update_module("c", new_code)

    assert hasattr(c, "func_c")
    assert hasattr(c, "C")
    assert callable(c.func_c)
    assert callable(c.C().func_c)
    c.func_c()
    assert c.C().func_c() == "C did something updated"  # Updated state
    assert a.A().func_c() == "C did something updated"  # Check if a is affected


def test_local_module_d_import():
    import a  # noqa: F401
    from d import a_lazy_import

    assert a_lazy_import() == "A did something"

    new_code = """
import b
from c import C

def func_a():
    print("Function A")

class A:
    def __init__(self):
        self.b = b.B()
        self.c = C()

    def do_something(self):
        self.b.func_b()
        return "A did something updated"

    def func_c(self):
        return self.c.func_c()
"""
    update_module("a", new_code)

    assert a_lazy_import() == "A did something updated"
