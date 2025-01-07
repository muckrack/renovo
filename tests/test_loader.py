import os
import sys
import tempfile
import unittest

from muckrack.hmr import HotModuleReplacement

reloader = HotModuleReplacement()


class TestHotModuleReloader(unittest.TestCase):
    def setUp(self):
        self.cleanup_modules(['a', 'b', 'c'])

    def tearDown(self):
        self.cleanup_modules(['a', 'b', 'c'])

    def cleanup_modules(self, module_names):
        for module_name in module_names:
            if module_name in sys.modules:
                del sys.modules[module_name]

    def test_initial_import(self):
        import a

        print(dir(a))  # Debug statement
        self.assertTrue(hasattr(a, 'func_a'))
        self.assertTrue(hasattr(a, 'A'))
        self.assertTrue(callable(a.func_a))
        self.assertTrue(callable(a.A().do_something))
        self.assertEqual(a.A().do_something(), "A did something")

    def test_reload_on_change(self):
        import a

        print(dir(a))  # Debug statement
        a.func_a()
        self.assertEqual(a.A().do_something(), "A did something")
        # Simulate change and reload
        print(reloader.dependency_graph)
        reloader.reload_module('a')
        self.assertTrue(hasattr(a, 'func_a'))
        self.assertTrue(hasattr(a, 'A'))
        self.assertTrue(callable(a.func_a))
        self.assertTrue(callable(a.A().do_something))
        self.assertEqual(a.A().do_something(), "A did something")

    def test_dependency_reload(self):
        import a
        import b
        import c

        c.a = None  # pyright: ignore [reportAttributeAccessIssue]
        print(dir(a))  # Debug statement
        a.func_a()
        self.assertEqual(a.A().do_something(), "A did something")
        b.func_b()
        b.B().func_b()
        c.func_c()
        c.C().func_c()
        # Simulate change and reload
        reloader.reload_module('c')
        print(dir(a))  # Debug statement
        self.assertTrue(hasattr(a, 'func_a'))
        self.assertTrue(hasattr(a, 'A'))
        self.assertTrue(callable(a.func_a))
        self.assertTrue(callable(a.A().do_something))
        self.assertEqual(a.A().do_something(), "A did something")
        self.assertTrue(hasattr(b, 'func_b'))
        self.assertTrue(hasattr(b, 'B'))
        self.assertTrue(callable(b.func_b))
        self.assertTrue(callable(b.B().func_b))
        self.assertTrue(hasattr(c, 'func_c'))
        self.assertTrue(hasattr(c, 'C'))
        self.assertTrue(callable(c.func_c))
        self.assertTrue(callable(c.C().func_c))

    def test_circular_dependency(self):
        # Simulate circular dependency
        import a
        import c

        c.a = a  # pyright: ignore [reportAttributeAccessIssue]
        print(dir(a))  # Debug statement
        a.func_a()
        self.assertEqual(a.A().do_something(), "A did something")
        c.func_c()
        c.C().func_c()
        self.assertTrue(hasattr(a, 'func_a'))
        self.assertTrue(hasattr(a, 'A'))
        self.assertTrue(callable(a.func_a))
        self.assertTrue(callable(a.A().do_something))
        self.assertTrue(hasattr(c, 'func_c'))
        self.assertTrue(hasattr(c, 'C'))
        self.assertTrue(callable(c.func_c))
        self.assertTrue(callable(c.C().func_c))
        # Simulate change and reload
        reloader.reload_module('c')
        print(dir(a))  # Debug statement
        self.assertTrue(hasattr(a, 'func_a'))
        self.assertTrue(hasattr(a, 'A'))
        self.assertTrue(callable(a.func_a))
        self.assertTrue(callable(a.A().do_something))
        self.assertEqual(a.A().do_something(), "A did something")
        self.assertTrue(hasattr(c, 'func_c'))
        self.assertTrue(hasattr(c, 'C'))
        self.assertTrue(callable(c.func_c))
        self.assertTrue(callable(c.C().func_c))

    def test_update_module_a(self):
        import a

        self.assertEqual(a.A().do_something(), "A did something")  # Initial state

        with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
            temp_file.write(b"""
def func_a():
    print("Updated Function A")

class A:
    def do_something(self):
        print("Updated A method")
        return "A did something updated"
""")
            temp_file_path = temp_file.name

        original_a_path = os.path.join(os.path.dirname(__file__), 'a.py')
        os.rename(original_a_path, original_a_path + '.bak')
        os.rename(temp_file_path, original_a_path)

        try:
            reloader.reload_module('a')
            self.assertTrue(hasattr(a, 'func_a'))
            self.assertTrue(hasattr(a, 'A'))
            self.assertTrue(callable(a.func_a))
            self.assertTrue(callable(a.A().do_something))
            a.func_a()
            self.assertEqual(a.A().do_something(), "A did something updated")  # Updated state
        finally:
            os.rename(original_a_path, temp_file_path)
            os.rename(original_a_path + '.bak', original_a_path)
            os.remove(temp_file_path)

    def test_update_module_c(self):
        import a
        import c

        self.assertEqual(c.C().func_c(), "C did something", "Initial state")  # Initial state

        with tempfile.NamedTemporaryFile(delete=False, suffix='.py') as temp_file:
            temp_file.write(b"""
def func_c():
    print("Updated Function C")

class C:
    def func_c(self):
        return "C did something updated"
""")
            temp_file_path = temp_file.name

        original_c_path = os.path.join(os.path.dirname(__file__), 'c.py')
        os.rename(original_c_path, original_c_path + '.bak')
        os.rename(temp_file_path, original_c_path)

        try:
            reloader.reload_module('c')
            self.assertTrue(hasattr(c, 'func_c'))
            self.assertTrue(hasattr(c, 'C'))
            self.assertTrue(callable(c.func_c))
            self.assertTrue(callable(c.C().func_c))
            c.func_c()
            self.assertEqual(
                c.C().func_c(), "C did something updated", "c.C().func_c() did not update"
            )  # Updated state
            self.assertEqual(
                a.A().func_c(), "C did something updated", "a.A().func_c() did not update"
            )  # Check if a is affected
        finally:
            os.rename(original_c_path, temp_file_path)
            os.rename(original_c_path + '.bak', original_c_path)
            os.remove(temp_file_path)
