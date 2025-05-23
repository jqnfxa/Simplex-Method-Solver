from PyQt5.QtCore import Qt, pyqtSlot
from PyQt5.QtGui import QBrush, QColor
from PyQt5.QtWidgets import QWidget, QTableWidget, QTableWidgetItem, QVBoxLayout, QMessageBox

from atom import Atom, LineEntry
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

        self.table_widget = QTableWidget()
        self.table_widget.setRowCount(1)
        self.table_widget.setColumnCount(3)
        self.table_widget.setHorizontalHeaderLabels(self.__header_row)
        self.table_widget.setVerticalHeaderLabels(self.__header_column)

        for i in range(2):
            self.table_widget.setItem(0, i, QTableWidgetItem('1'))
        item = QTableWidgetItem('0')
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(0, 2, item)
        self.__atom.grad = [0, 1, 0]

        layout = QVBoxLayout()
        layout.addWidget(self.table_widget)
        self.setLayout(layout)

        self.table_widget.itemChanged.connect(self.data_changed)  # type: ignore

        self.update_column_widths()
        self.table_widget.horizontalHeader().sectionResized.connect(self.update_column_widths)
        self.resizeEvent = self.onResize

    def onResize(self, event):
        """
        Event handler to update column widths when the table is resized
        """
        super().resizeEvent(event)
        self.update_column_widths()

    def update_column_widths(self):
        """Calculates and sets column widths based on the available space."""
        # Get the total width of the table (adjusting for scrollbars if present)
        total_width = self.table_widget.viewport().width()

        # Distribute width proportionally (e.g., 33% for each column).
        column_width = total_width // self.table_widget.columnCount()

        for i in range(self.table_widget.columnCount()):
            self.table_widget.setColumnWidth(i, column_width)

    def update_labels(self):
        labels = [f"y{row}" for row in range(1, self.table_widget.rowCount())]
        labels.append('f')
        self.table_widget.setHorizontalHeaderLabels(self.__header_row)
        self.table_widget.setVerticalHeaderLabels(labels)

    def update_from_info(self, info: Info):
        # disconnect update function
        self.table_widget.itemChanged.disconnect(self.data_changed)  # type: ignore

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
        row = self.table_widget.rowCount() - 1
        col = self.table_widget.columnCount() - 1
        item = QTableWidgetItem(str(round(info.optimum, 2)))
        item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        self.table_widget.setItem(row, col, item)

        # labels
        self.table_widget.setHorizontalHeaderLabels(info.row)
        column_labels = info.column
        self.table_widget.setVerticalHeaderLabels(column_labels)

        # reconnect update function
        self.table_widget.itemChanged.connect(self.data_changed)  # type: ignore

    def insert_row(self):
        if self.__atom.state != ProgramState.Modification:
            return

        # disconnect update function
        self.table_widget.itemChanged.disconnect(self.data_changed)  # type: ignore

        row_idx = self.table_widget.rowCount() - 1
        self.table_widget.insertRow(row_idx)
        self.update_labels()

        for col in range(self.table_widget.columnCount()):
            item = QTableWidgetItem('0')
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table_widget.setItem(row_idx, col, item)

        # reconnect update function
        self.table_widget.itemChanged.connect(self.data_changed)  # type: ignore

        # add associated row
        self.__atom.lines.append(LineEntry(0, 0, 0, Line(Point(0, 0), Point(0, 0))))
        self.__atom.remove_observer(self)
        self.__atom.notify_observers()
        self.__atom.add_observer(self)

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
            self.__atom.lines.pop(current_row)
            self.__atom.remove_observer(self)
            self.__atom.notify_observers()
            self.__atom.add_observer(self)

    @pyqtSlot(QTableWidgetItem)
    def data_changed(self, item):
        if self.__atom.state != ProgramState.Modification:
            return

        row = item.row()
        col = item.column()
        value = self.table_widget.item(row, col).text()

        if not is_float(value):
            QMessageBox.critical(self, "Ошибка", f"Элемент таблицы не является вещественным числом: {value}")
            item = QTableWidgetItem('0')
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
            self.table_widget.setItem(row, col, item)
            return

        # disconnect update function
        self.table_widget.itemChanged.disconnect(self.data_changed)  # type: ignore

        row_data = []
        for c in range(self.table_widget.columnCount()):
            row_data.append(self.table_widget.item(row, c))
        row_data = decode_row(row_data)

        # ignore invalid input (use old values)
        if not all(is_float(x) for x in row_data):
            return

        # gradient
        if row + 1 == self.table_widget.rowCount():
            self.__atom.grad = list(map(float, row_data))
        else:
            x1, x2, b = map(float, row_data)
            self.__atom.lines[row] = LineEntry(x1, x2, b, shrink_line(table_row_to_vector(x1, x2, b, lim=self.__atom.lim)))

        # reconnect update function
        self.table_widget.itemChanged.connect(self.data_changed)  # type: ignore
        self.__atom.remove_observer(self)
        self.__atom.notify_observers()
        self.__atom.add_observer(self)

    def update(self):
        if self.__atom.state != ProgramState.Modification:
            return

        # disconnect update function
        self.table_widget.itemChanged.disconnect(self.data_changed)  # type: ignore

        while self.table_widget.rowCount() > 0:
            self.table_widget.removeRow(0)

        for i in range(len(self.__atom.lines)):
            row_idx = self.table_widget.rowCount()
            self.table_widget.insertRow(row_idx)

            data = self.__atom.lines[i].coeffs
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
        self.table_widget.itemChanged.connect(self.data_changed)  # type: ignore
