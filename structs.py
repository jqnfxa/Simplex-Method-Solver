import math
from enum import Enum
from typing import NamedTuple


class ProgramState(Enum):
    Modification = 1
    Viewing = 2


class Point(NamedTuple):
    x: float
    y: float


class Line(NamedTuple):
    begin: Point
    end: Point

    def is_vertical(self, tol=1e-6) -> bool:
        return abs(self.begin.x - self.end.x) < tol

    def is_horizontal(self, tol=1e-6) -> bool:
        return abs(self.begin.y - self.end.y) < tol

    def grad(self):
        dx = self.end.x - self.begin.x
        dy = self.end.y - self.begin.y
        norm_factor = math.sqrt(dx * dx + dy * dy)
        if norm_factor < 1e-6:
            norm_factor = 1

        return -dy / norm_factor, dx / norm_factor
