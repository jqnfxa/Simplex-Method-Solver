from structs import Point, Line
import numpy as np


# Formalisation
# row: x1 * x + x2 * y + b = 0
def line_to_table_row(line: Line, rounding=4):
    # vertical line
    if line.is_vertical():
        x1, x2, b = 1, 0, round(-line.begin.x, rounding)
        if line.end.y > line.begin.y:
            x1 *= -1
            b *= -1

    # horizontal line
    elif line.is_horizontal():
        x1, x2, b = 0, 1, round(-line.begin.y, rounding)
        if line.end.x > line.begin.x:
            x2 *= -1
            b *= -1

    # regular line
    else:
        x1 = line.begin.y - line.end.y
        x2 = line.end.x - line.begin.x
        b = line.begin.x * line.end.y - line.end.x * line.begin.y
        x1, x2, b = round(x1, rounding), round(x2, rounding), round(b, rounding)

    return x1, x2, b


def table_row_to_line(x1: float, x2: float, b: float, lims: [float, float]) -> Line:
    tol = 1e-6

    # invalid row
    if abs(x1) < tol and abs(x2) < tol:
        return Line(Point(0, 0), Point(0, 0))

    # horizontal line
    if abs(x1) < tol:
        return Line(Point(0, -b / x2), Point(lims[0], (-b - x1 * lims[0]) / x2))

    # vertical line
    if abs(x2) < tol:
        return Line(Point(-b / x1, 0), Point((-b - x2 * lims[1]) / x1, lims[1]))

    # regular line
    point1 = Point(0, -b / x2)
    point2 = Point(-b / x1, 0)
    point3 = Point(lims[0], (-b - x1 * lims[0]) / x2)
    point4 = Point((-b - x2 * lims[1]) / x1, lims[1])

    # choose points such as
    # 1,2 ; 1,3 ; 1,4
    if 0 <= point1.y <= lims[1]:
        if 0 <= point2.x <= lims[0]:
            return Line(point1, point2)
        if 0 <= point3.y <= lims[1]:
            return Line(point1, point3)
        return Line(point1, point4)

    # 2,3 ; 2,4
    if 0 <= point2.x <= lims[0]:
        if 0 <= point3.y <= lims[1]:
            return Line(point2, point3)
        return Line(point2, point4)

    # 3,4
    return Line(point3, point4)


def table_row_to_vector(x1: float, x2: float, b: float, lims: [float, float]) -> Line:
    line = table_row_to_line(x1, x2, b, lims)

    if abs(x1) < 1e-6:
        sign = x2 * b
    elif abs(x2) < 1e-6:
        sign = x1 * b
    else:
        sign = x1 * x2 * b
    return Line(line.end, line.begin) if sign < 0 else line


def shrink_line(line: Line, factor: float = 0.8) -> Line:
    if factor > 1 or factor <= 0:
        return line

    m = (1 - factor) / 2
    ab = np.array([line.end.x - line.begin.x, line.end.y - line.begin.y], dtype=float)
    aa_prime = m * ab
    a_prime = Point(line.begin.x + float(aa_prime[0]), line.begin.y + float(aa_prime[1]))
    ba = -ab
    bb_prime = m * ba
    b_prime = Point(line.end.x + float(bb_prime[0]), line.end.y + float(bb_prime[1]))
    return Line(a_prime, b_prime)
