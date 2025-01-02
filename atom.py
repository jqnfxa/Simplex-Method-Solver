from structs import ProgramState


class Atom:
    def __init__(self, state: ProgramState, lines: list[list], grad: list[float], lims: list[float]):
        self.state = state
        self.lines = lines
        self.grad = grad
        self.lims = lims
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

    def set_lines(self, lines: list[list]):
        self.lines = lines
        self.notify_observers()

    def set_grad(self, grad: list[float]):
        self.grad = grad
        self.notify_observers()

    def set_lims(self, lims: list[float]):
        self.lims = lims
        self.notify_observers()
