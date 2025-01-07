import c


def func_b():
    print("Function B")


class B:
    def __init__(self):
        self.c = c.C()

    def func_b(self):
        print("Class B method")
        self.c.func_c()
