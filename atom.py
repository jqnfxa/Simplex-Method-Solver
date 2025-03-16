from structs import ProgramState, Line


class LineEntry:
    def __init__(self, x1: float, x2: float, b: float, line: Line):
        self.coeffs = [x1, x2, b]
        self.line = line


class Atom:
    def __init__(self, state: ProgramState, lines: list[LineEntry], grad: list[float], lim: float):
        self.state = state
        self.lines = lines
        self.grad = grad
        self.lim = lim
        self.observers = []

    def add_observer(self, observer):
        self.observers.append(observer)

    def remove_observer(self, observer):
        self.observers.remove(observer)

    def notify_observers(self):
        for observer in self.observers:
            observer.update()

    def set_state(self, state: ProgramState):
        self.state = state
        self.notify_observers()

    def set_lines(self, lines: list[LineEntry]):
        self.lines = lines
        self.notify_observers()

    def set_grad(self, grad: list[float]):
        self.grad = grad
        self.notify_observers()

    def set_lims(self, lim: float):
        self.lim = lim
        self.notify_observers()
