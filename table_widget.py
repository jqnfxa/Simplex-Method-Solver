import numpy as np
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout

from atom import Atom
from equations import table_row_to_vector, shrink_line
from simplex import Info
from structs import Point, Line, ProgramState


def is_float(element: any) -> bool:
    if element is None:
        return False
    try:
        float(element)
        return True
    except ValueError:
        return False


def decode_row(row) -> list:
    decoded_row = []
    for item in row:
        if item and is_float(item.text()):
            decoded_row.append(item.text())
        else:
            decoded_row.append(None)
    return decoded_row


class TableWidget(QWidget):
    def __init__(self, atom: Atom):
        super().__init__()
        self.__atom = atom
        self.__header_row = ['x1', 'x2', '-b']
        self.__header_column = ['f']
        self.__header_widths = [120, 120, 120]

        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(self.__header_row)
        self.table_widget.setVerticalHeaderLabels(self.__header_column)

        for i, width in enumerate(self.__header_widths):
            self.table_widget.setColumnWidth(i, width)
        for i in range(2):
            self.table_widget.setItem(0, i, QTableWidgetItem('1'))
        item = QTableWidgetItem('0')
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(0, 2, item)
        self.__atom.grad = [1, 1, 0]

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

        self.table_widget.itemChanged.connect(self.data_changed)

    def update_labels(self):
        labels = [f"y{row}" for row in range(1, self.table_widget.rowCount())]
        labels.append('f')
        self.table_widget.setHorizontalHeaderLabels(self.__header_row)
        self.table_widget.setVerticalHeaderLabels(labels)

    def update_from_info(self, info: Info):
        # disconnect update function
        self.table_widget.itemChanged.disconnect(self.data_changed)

        while self.table_widget.rowCount() > 0:
            self.table_widget.removeRow(0)

        table = info.table
        for i in range(len(table) - 1):
            row_idx = self.table_widget.rowCount()
            self.table_widget.insertRow(row_idx)

            data = table[i]
            for col in range(self.table_widget.columnCount()):
                item = QTableWidgetItem(str(round(data[col], 2)) if is_float(data[col]) else '0')
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)

                # highlight important element
                if row_idx == info.i and col == info.j:
                    item.setBackground(QBrush(QColor(255, 0, 0)))

                self.table_widget.setItem(row_idx, col, item)

        # gradient
        row_idx = self.table_widget.rowCount()
        self.table_widget.insertRow(row_idx)

        data = table[-1]
        for col in range(self.table_widget.columnCount() - 1):
            item = QTableWidgetItem(str(round(data[col], 2)) if is_float(data[col]) else '0')
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table_widget.setItem(row_idx, col, item)
        item = QTableWidgetItem('0')
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(row_idx, 2, item)

        # optimal point
        row_idx = self.table_widget.rowCount()
        self.table_widget.insertRow(row_idx)

        item = QTableWidgetItem(str(round(info.x1, 2)))
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(row_idx, 0, item)
        item = QTableWidgetItem(str(round(info.x2, 2)))
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(row_idx, 1, item)
        item = QTableWidgetItem(str(round(info.optimum, 2)))
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(row_idx, 2, item)

        # labels
        self.table_widget.setHorizontalHeaderLabels(info.row)
        column_labels = info.column
        column_labels.append('p')
        self.table_widget.setVerticalHeaderLabels(column_labels)

        # reconnect update function
        self.table_widget.itemChanged.connect(self.data_changed)

    def insert_row(self):
        if self.__atom.state != ProgramState.Modification:
            return

        # disconnect update function
        self.table_widget.itemChanged.disconnect(self.data_changed)

        row_idx = self.table_widget.rowCount() - 2
        self.table_widget.insertRow(row_idx)
        self.update_labels()

        for col in range(self.table_widget.columnCount()):
            item = QTableWidgetItem('0')
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table_widget.setItem(row_idx, col, item)

        # reconnect update function
        self.table_widget.itemChanged.connect(self.data_changed)

        # add associated row
        lines = self.__atom.lines
        lines.append([0, 0, 0, Line(Point(0, 0), Point(0, 0))])
        self.__atom.set_lines(lines)

    def remove_row(self):
        if self.__atom.state != ProgramState.Modification:
            return

        current_row = self.table_widget.currentRow()
        if current_row >= self.table_widget.rowCount():
            return
        if current_row == self.table_widget.rowCount() - 1:
            current_row -= 1
        if current_row >= 0:
            self.table_widget.removeRow(current_row)
            self.update_labels()

            # remove associated row
            lines = self.__atom.lines
            lines.pop(current_row)
            self.__atom.set_lines(lines)

    def data_changed(self):
        if self.__atom.state != ProgramState.Modification:
            return

        # disconnect update function
        self.table_widget.itemChanged.disconnect(self.data_changed)

        lines = []
        for i in range(self.table_widget.rowCount() - 1):
            row_data = []
            for col in range(self.table_widget.columnCount()):
                row_data.append(self.table_widget.item(i, col))
            row_data = decode_row(row_data)

            if all(is_float(x) for x in row_data):
                x1, x2, b = map(float, row_data)
                row_data.append(shrink_line(table_row_to_vector(x1, x2, b, lims=self.__atom.lims)))
            else:
                x1, x2, b = map(float, [0, 0, 0])
                row_data.append(shrink_line(table_row_to_vector(x1, x2, b, lims=self.__atom.lims)))
                row_data.append(Line(Point(0, 0), Point(0, 0)))
            lines.append(row_data)

        # gradient
        row_data = []
        for col in range(self.table_widget.columnCount() - 1):
            row_data.append(self.table_widget.item(self.table_widget.rowCount() - 1, col))
        row_data = decode_row(row_data)

        if all(is_float(x) for x in row_data):
            grad = list(map(float, row_data))
            grad.append(0)
        else:
            grad = self.__atom.grad

        # reconnect update function
        self.table_widget.itemChanged.connect(self.data_changed)

        self.__atom.grad = grad
        self.__atom.set_lines(lines)

    def update(self):
        if self.__atom.state != ProgramState.Modification:
            return

        # disconnect update function
        self.table_widget.itemChanged.disconnect(self.data_changed)

        while self.table_widget.rowCount() > 0:
            self.table_widget.removeRow(0)

        for i in range(len(self.__atom.lines)):
            row_idx = self.table_widget.rowCount()
            self.table_widget.insertRow(row_idx)

            data = self.__atom.lines[i][:3]
            for col in range(self.table_widget.columnCount()):
                item = QTableWidgetItem(str(data[col]) if is_float(data[col]) else '0')
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                self.table_widget.setItem(row_idx, col, item)

        # gradient
        row_idx = self.table_widget.rowCount()
        self.table_widget.insertRow(row_idx)

        data = self.__atom.grad
        for col in range(self.table_widget.columnCount() - 1):
            item = QTableWidgetItem(str(data[col]) if is_float(data[col]) else '0')
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table_widget.setItem(row_idx, col, item)
        item = QTableWidgetItem('0')
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(row_idx, 2, item)

        # labels
        self.update_labels()

        # reconnect update function
        self.table_widget.itemChanged.connect(self.data_changed)
