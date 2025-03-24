import math
from PyQt5.QtWidgets import QVBoxLayout, QWidget
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import numpy as np
import time

from matplotlib.figure import Figure
from matplotlib.ticker import MultipleLocator

from atom import Atom, LineEntry
from equations import line_to_table_row, table_row_to_vector, shrink_line
from structs import ProgramState, Line, Point


def distance_between_points(p1, p2):
    return np.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)


def distance_point_to_line(x, y, x1, y1, x2, y2):
    return abs((y2 - y1) * x - (x2 - x1) * y + x2 * y1 - y2 * x1) / np.sqrt((y2 - y1) ** 2 + (x2 - x1) ** 2)


def is_point_on_line(x, y, line: Line, tolerance=0.1):
    x1, y1 = line.begin
    x2, y2 = line.end
    return distance_point_to_line(x, y, x1, y1, x2, y2) < tolerance


def is_point_on_point(x, y, point: Point, tolerance=0.2):
    if point is None:
        return False
    return distance_between_points(Point(x, y), Point(point.x, point.y)) < tolerance


def gradient_point(line: Line, scale=1.0) -> Point:
    x1, y1 = line.begin
    x2, y2 = line.end
    mid_x = (x1 + x2) / 2
    mid_y = (y1 + y2) / 2

    dx = x2 - x1
    dy = y2 - y1

    norm_factor = math.sqrt(dx * dx + dy * dy)
    if norm_factor < 1e-4:
        norm_factor = 1

    return Point(mid_x - dy / norm_factor * scale, mid_y + dx / norm_factor * scale)


class PlotWidget(QWidget):
    def __init__(self, atom: Atom):
        super().__init__()
        self.selected_gradient = False
        self.gradient_color = 'red'
        self.__atom = atom

        self.default_line_color = 'blue'
        self.default_point_color = 'red'
        self.selected_line_color = 'green'
        self.gradient_line_color = 'red'
        self.gradient_function_color = 'blue'
        self.optimal_point_color = 'red'
        self.pptol = 0.15
        self.pltol = 0.15
        self.min_scale = 10

        self.xmul = 0.1
        self.ymul = 0.1

        self.figure = Figure(dpi=300)
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        self.update_grid()

        self.canvas.mpl_connect('button_press_event', self.on_click)  # type: ignore
        self.canvas.mpl_connect('motion_notify_event', self.on_drag)  # type: ignore
        self.canvas.mpl_connect('button_release_event', self.on_release)  # type: ignore

        layout = QVBoxLayout()
        layout.addWidget(self.canvas)
        self.setLayout(layout)

        self.colors = ['blue'] * len(self.__atom.lines)
        self.modifying = False
        self.first_point = None
        self.temp_line = None
        self.selected_line = None
        self.dragging_point = None
        self.dragging_line = None
        self.drag_start_point = None
        self.last_click_time = 0

        # delay in seconds for double-click detection
        self.double_click_delay = 0.300

        # tolerance to determine if points are too close
        self.drag_tolerance = 0.5

    def update_grid(self):
        tl = 2 * self.__atom.lim / 100 # 2%
        self.ax.set_xlim(0 - tl, self.__atom.lim)
        self.ax.set_ylim(0 - tl, self.__atom.lim)
        self.ax.set_aspect('equal')
        self.ax.grid(True)

        # set major ticks
        self.ax.xaxis.set_major_locator(MultipleLocator(self.__atom.lim * self.xmul))
        self.ax.yaxis.set_major_locator(MultipleLocator(self.__atom.lim * self.ymul))

        # set minor ticks
        self.ax.xaxis.set_minor_locator(MultipleLocator(self.__atom.lim * self.xmul / 2))
        self.ax.yaxis.set_minor_locator(MultipleLocator(self.__atom.lim * self.ymul / 2))
        self.ax.grid(True, which='both')

    def scale(self):
        return self.__atom.lim / self.min_scale

    def update_canvas(self):
        self.update_lines()

    def update(self):
        if self.__atom.state == ProgramState.Modification:
            self.update_grid()
            self.update_canvas()
            self.canvas.draw()
        else:
            self.update_grid()

    def remove_line(self, event):
        if self.__atom.state != ProgramState.Modification:
            return
        if self.selected_line is None:
            return
        if self.modifying:
            idx = self.selected_line
            self.selected_line = None
            self.dragging_point = None
            self.dragging_line = None
            self.modifying = False
            self.first_point = None
            self.temp_line = None
            self.__atom.lines.pop(idx)
            self.__atom.notify_observers()

    def on_left_mouse_press(self, event):
        if self.__atom.state != ProgramState.Modification:
            return

        if self.selected_gradient:
            return

        current_time = time.time()
        if self.last_click_time is not None and current_time - self.last_click_time < self.double_click_delay:
            # double-click detected
            self.on_double_click(event)
            self.last_click_time = None
            return
        self.last_click_time = current_time

        if not self.modifying and self.selected_line is not None:
            self.modifying = True

        if self.modifying:
            # if modifying, check if we are clicking on a point to drag
            self.dragging_point = None

            for i in range(len(self.__atom.lines)):
                line: Line = self.__atom.lines[i].line
                if is_point_on_point(event.xdata, event.ydata, line.begin, tolerance=self.pptol * self.scale()):
                    self.dragging_point = 0
                    self.drag_start_point = (event.xdata, event.ydata)
                if is_point_on_point(event.xdata, event.ydata, line.end, tolerance=self.pptol * self.scale()):
                    self.dragging_point = 1
                    self.drag_start_point = (event.xdata, event.ydata)

                if self.dragging_point is not None:
                    break

            if self.dragging_point is None:
                # check if we are clicking on the line itself to drag the entire line
                for i in range(len(self.__atom.lines)):
                    if is_point_on_line(event.xdata, event.ydata, self.__atom.lines[i].line, tolerance=self.pltol * self.scale()):
                        self.selected_line = i
                        self.dragging_line = i
                        self.drag_start_point = (event.xdata, event.ydata)
                        self.update_lines()
                        return

        elif not self.modifying and self.first_point is None:
            self.first_point = Point(event.xdata, event.ydata)
            self.temp_line = Line(self.first_point, self.first_point)

    def on_right_mouse_press(self):
        if self.__atom.state != ProgramState.Modification:
            return

        if self.selected_gradient:
            self.selected_gradient = False
            self.gradient_color = self.gradient_function_color
            self.__atom.notify_observers()
            return

        if self.selected_line is not None:
            self.colors[self.selected_line] = self.default_line_color

        self.selected_line = None
        self.dragging_point = None
        self.dragging_line = None
        self.modifying = False
        self.first_point = None
        self.temp_line = None
        self.colors = [self.default_line_color] * len(self.__atom.lines)

        for i in range(len(self.__atom.lines)):
            self.__atom.lines[i].coeffs = list(map(float, line_to_table_row(self.__atom.lines[i].line, 2)))
        for i in range(len(self.__atom.lines)):
            if self.__atom.lines[i].line.begin.x < 0 or self.__atom.lines[i].line.begin.x > self.__atom.lim or \
                    self.__atom.lines[i].line.begin.y < 0 or self.__atom.lines[i].line.begin.y > self.__atom.lim or \
                    self.__atom.lines[i].line.end.x < 0 or self.__atom.lines[i].line.end.x > self.__atom.lim or \
                    self.__atom.lines[i].line.end.y < 0 or self.__atom.lines[i].line.end.y > self.__atom.lim:
                self.__atom.lines[i].line = shrink_line(table_row_to_vector(*self.__atom.lines[i].coeffs, self.__atom.lim))

        # call update
        self.__atom.notify_observers()

    def on_click(self, event):
        if self.__atom.state != ProgramState.Modification:
            return

        # left mouse button
        if event.button == 1:
            self.on_left_mouse_press(event)

        # right mouse button
        elif event.button == 3:
            self.on_right_mouse_press()

    def on_double_click(self, event):
        if self.__atom.state != ProgramState.Modification:
            return

        # check if double-click is on the gradient vector
        x0 = self.__atom.lim / 2
        y0 = self.__atom.lim / 2
        grad_x, grad_y = self.__atom.grad[:-1]
        norm_factor = math.sqrt(grad_x * grad_x + grad_y * grad_y)
        if norm_factor < 1e-4:
            norm_factor = 1
        dir_x = grad_x / norm_factor * 1.5 * self.scale()
        dir_y = grad_y / norm_factor * 1.5 * self.scale()
        gradient_end_point = Point(x0 + dir_x, y0 + dir_y)

        if is_point_on_point(event.xdata, event.ydata, gradient_end_point, tolerance=self.pptol * self.scale()):
            self.selected_gradient = True
            self.gradient_color = self.selected_line_color
            self.update_lines()
            return

        self.modifying = False
        for i in range(len(self.__atom.lines)):
            # update selected line if double click detected
            current_line: Line = self.__atom.lines[i].line
            if is_point_on_line(event.xdata, event.ydata, current_line, tolerance=self.pltol * self.scale()):
                if self.selected_line != i:
                    if self.selected_line:
                        self.colors[self.selected_line] = self.default_line_colorr
                    self.selected_line = i
                    self.colors[self.selected_line] = self.selected_line_color
                    self.modifying = True
                self.update_lines()
                return

            # update gradient if clicked
            if is_point_on_point(event.xdata, event.ydata, gradient_point(current_line, self.scale()), tolerance=self.pptol * self.scale()):
                self.__atom.lines[i].line = Line(
                    self.__atom.lines[i].line.end,
                    self.__atom.lines[i].line.begin
                )
                self.__atom.lines[i].coeffs = list(map(float, line_to_table_row(self.__atom.lines[i].line, 2)))
                self.__atom.notify_observers()
                return

    def on_drag(self, event):
        if self.__atom.state != ProgramState.Modification:
            return
        if event.button != 1:
            return

        if event.xdata is None or event.ydata is None:
            self.selected_line = None
            self.dragging_point = None
            self.dragging_line = None
            self.modifying = False
            self.first_point = None
            self.temp_line = None
            if self.selected_gradient:
                self.selected_gradient = False
                self.gradient_color = self.gradient_function_color
            self.update_lines()
            return

        if self.selected_gradient:
            dx = round(event.xdata - self.__atom.lim / 2, 2)
            dy = round(event.ydata - self.__atom.lim / 2, 2)
            self.__atom.grad = [dx, dy, 0]
            self.update_lines()
            return

        if self.dragging_point is not None and self.selected_line is not None:
            # dragging a point of the selected line
            dx = event.xdata - self.drag_start_point[0]
            dy = event.ydata - self.drag_start_point[1]

            if self.dragging_point == 0:
                self.__atom.lines[self.selected_line].line = Line(
                    Point(
                        self.__atom.lines[self.selected_line].line.begin.x + dx,
                        self.__atom.lines[self.selected_line].line.begin.y + dy
                    ),
                    self.__atom.lines[self.selected_line].line.end,
                )
            elif self.dragging_point == 1:
                self.__atom.lines[self.selected_line].line = Line(
                    self.__atom.lines[self.selected_line].line.begin,
                    Point(
                        self.__atom.lines[self.selected_line].line.end.x + dx,
                        self.__atom.lines[self.selected_line].line.end.y + dy
                    )
                )
            self.drag_start_point = (event.xdata, event.ydata)

        elif self.dragging_point is None and self.dragging_line is not None and self.selected_line is not None:
            # dragging a line
            dx = event.xdata - self.drag_start_point[0]
            dy = event.ydata - self.drag_start_point[1]
            self.__atom.lines[self.selected_line].line = Line(
                Point(
                    self.__atom.lines[self.selected_line].line.begin.x + dx,
                    self.__atom.lines[self.selected_line].line.begin.y + dy
                ),
                Point(
                    self.__atom.lines[self.selected_line].line.end.x + dx,
                    self.__atom.lines[self.selected_line].line.end.y + dy
                )
            )
            self.drag_start_point = (event.xdata, event.ydata)

        elif self.dragging_point is None and self.temp_line is not None:
            self.temp_line = Line(self.first_point, Point(event.xdata, event.ydata))

        self.update_lines()

    def on_release(self, event):
        if self.__atom.state != ProgramState.Modification:
            return
        if event.button != 1:
            return
        if event.xdata is None or event.ydata is None:
            self.selected_line = None
            self.dragging_point = None
            self.dragging_line = None
            self.modifying = False
            self.first_point = None
            self.temp_line = None
            if self.selected_gradient:
                self.selected_gradient = False
                self.gradient_color = self.gradient_function_color
            self.colors = [self.default_line_color] * len(self.__atom.lines)
            self.update_lines()
            return

        if self.selected_gradient:
            return

        if self.dragging_point is not None and self.selected_line is not None:
            # finished dragging a point
            self.dragging_point = None
            self.update_lines()

        if self.dragging_line is not None and self.selected_line is not None:
            # finished dragging line
            self.dragging_line = None
            self.update_lines()

        # finished drawing a line
        elif not self.modifying and self.first_point is not None:
            if self.temp_line:
                self.temp_line = None

            second_point = Point(event.xdata, event.ydata)
            if distance_between_points(self.first_point, second_point) < self.drag_tolerance:
                # points are too close, don't draw the line
                self.first_point = None
                self.update_lines()
                return

            line = Line(self.first_point, second_point)
            x1, x2, b = line_to_table_row(line, 2)
            self.__atom.lines.append(LineEntry(x1, x2, b, line))
            self.colors = [self.default_line_color] * len(self.__atom.lines)
            self.first_point = None
            self.__atom.notify_observers()

    def highlight_points(self, line, markersize=3):
        self.ax.plot(line.begin.x, line.begin.y, color=self.default_point_color, marker='.', markersize=markersize)
        self.ax.plot(line.end.x, line.end.y, color=self.default_point_color, marker='.', markersize=markersize)

    def draw_lines(self, lines):
        self.update_grid()

        for line in lines:
            line_original = line
            x1, x2, b = map(float, line_to_table_row(line_original, 2))
            line = table_row_to_vector(x1, x2, b, self.__atom.lim)

            self.ax.plot([line_original.begin.x, line_original.end.x], [line_original.begin.y, line_original.end.y], color=self.default_line_color)
            self.ax.plot([line.begin.x, line.end.x], [line.begin.y, line.end.y], color=self.default_line_color)
            self.draw_gradient(line_original)

        self.canvas.draw()

    def draw_point(self, x, y, markersize=3):
        self.ax.plot(x, y, color=self.optimal_point_color, marker='s', markersize=markersize)

    def draw_vector(self, x, y):
        self.update_grid()
        norm_factor = math.sqrt(x * x + y * y)
        if norm_factor < 1e-4:
            norm_factor = 1

        dir_x = x / norm_factor * 1.5 * self.scale()
        dir_y = y / norm_factor * 1.5 * self.scale()
        x0 = self.__atom.lim / 2
        y0 = self.__atom.lim / 2

        self.ax.arrow(x0, y0, dir_x, dir_y, head_width=0.2 * self.scale(), head_length=0.1 * self.scale(), fc=self.gradient_color, ec=self.gradient_color, zorder=2)

    def update_lines(self):
        self.ax.clear()
        self.update_grid()

        if len(self.colors) != len(self.__atom.lines):
            self.colors = [self.default_line_color] * len(self.__atom.lines)

        for i in range(len(self.__atom.lines)):
            line = self.__atom.lines[i].line
            linev = table_row_to_vector(*line_to_table_row(line, 2), self.__atom.lim)

            self.ax.plot([linev.begin.x, linev.end.x], [linev.begin.y, linev.end.y], color=self.colors[i], lw=1)
            self.ax.plot([line.begin.x, line.end.x], [line.begin.y, line.end.y], color=self.colors[i], lw=2)
            self.highlight_points(line)
            self.draw_gradient(line)

        if self.temp_line is not None:
            line = self.temp_line
            self.ax.plot([line.begin.x, line.end.x], [line.begin.y, line.end.y], color='r')

        self.draw_vector(*self.__atom.grad[:-1])
        self.canvas.draw()

    def draw_gradient(self, line):
        x1, y1 = line.begin
        x2, y2 = line.end
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2

        dx = x2 - x1
        dy = y2 - y1

        norm_factor = math.sqrt(dx * dx + dy * dy)
        if norm_factor < 1e-6:
            norm_factor = 1

        dir_x = -dy / norm_factor * self.scale()
        dir_y = dx / norm_factor * self.scale()

        # draw the gradient arrow
        self.ax.arrow(mid_x, mid_y, dir_x, dir_y, head_width=0.12 * self.scale(), head_length=0.1 * self.scale(), fc=self.gradient_line_color, ec=self.gradient_line_color, zorder=2)
