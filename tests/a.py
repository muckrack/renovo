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
        return "A did something"

    def func_c(self):
        return self.c.func_c()
