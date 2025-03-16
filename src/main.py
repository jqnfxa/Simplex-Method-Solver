import copy
import sys

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QToolBar, QComboBox, QMessageBox, QSlider, QTableWidgetItem, QFileDialog
from PyQt5.QtCore import Qt

from atom import Atom, LineEntry
from equations import table_row_to_line, shrink_line, table_row_to_vector
from plot_widget import PlotWidget
from simplex import SimplexMethod, Error
from structs import ProgramState, Line, Point
from table_widget import TableWidget, is_float


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.grad = None
        self.lines_to_plot = None
        self.setWindowTitle("QtSimplex v.2025")

        # fullscreen mode
        screen_geometry = QApplication.screens()[0].availableGeometry()
        width = screen_geometry.width()
        height = screen_geometry.height()
        self.setGeometry(0, 0, width, height)

        # modifiable data
        self._atom = Atom(ProgramState.Modification, [], [0, 1, 0], 10)

        # widgets
        self.table_widget = TableWidget(self._atom)
        self.plot_widget = PlotWidget(self._atom)
        self.last_atom = None
        self.tables = None
        self.lines = None

        # reactive reaction
        self._atom.add_observer(self.table_widget)
        self._atom.add_observer(self.plot_widget)

        # solution combo box
        self.combo_box = QComboBox()

        self.state_button = QPushButton('Перейти к решению')
        self.state_button.clicked.connect(self.switch_state)  # type: ignore

        self.insert_row_button = QPushButton('Добавить условие')
        self.insert_row_button.clicked.connect(self.table_widget.insert_row)  # type: ignore

        self.remove_row_button = QPushButton('Удалить условие')
        self.remove_row_button.clicked.connect(self.table_widget.remove_row)  # type: ignore
        self.remove_row_button.clicked.connect(self.plot_widget.remove_line)  # type: ignore

        # slider for limits
        self.limit_slider = QSlider(Qt.Horizontal)
        self.limit_slider.setMinimum(10)
        self.limit_slider.setMaximum(100)
        self.limit_slider.setValue(10)  # Initial value
        self.limit_slider.valueChanged.connect(self.update_limits)  # type: ignore

        # save/load buttons
        self.save_button = QPushButton('Сохранить файл')
        self.save_button.clicked.connect(self.save_state)  # type: ignore
        self.load_button = QPushButton('Загрузить файл')
        self.load_button.clicked.connect(self.load_state)  # type: ignore

        # toolbar with buttons
        toolbar = QToolBar()
        toolbar.addWidget(self.combo_box)
        toolbar.addWidget(self.state_button)
        toolbar.addWidget(self.insert_row_button)
        toolbar.addWidget(self.remove_row_button)
        toolbar.addWidget(self.limit_slider)
        toolbar.addWidget(self.save_button)
        toolbar.addWidget(self.load_button)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.table_widget, 2)
        main_layout.addWidget(self.plot_widget, 8)

        container_layout = QVBoxLayout()
        container_layout.addLayout(main_layout)

        container = QWidget()
        container.setLayout(container_layout)
        self.setCentralWidget(container)
        self._atom.notify_observers()

    def update_limits(self, value):
        self._atom.lim = value
        self.plot_widget.update()

    def compute_solution(self):
        y = []
        for row in self._atom.lines:
            y.append(list(map(float, row.coeffs)))
        c = copy.deepcopy(self._atom.grad)[:-1]
        self.tables = SimplexMethod(y, c).get_solution()
        self.lines = []
        for line in y:
            self.lines.append(table_row_to_line(*line, self._atom.lim))
        self.grad = self._atom.grad[:-1]

    def on_combo_box_changed(self, index):
        if index != -1:
            self.table_widget.update_from_info(self.tables[index])
            self.plot_widget.ax.clear()
            self.plot_widget.draw_vector(*self.grad)
            self.plot_widget.draw_lines(self.lines_to_plot)
            self.plot_widget.draw_point(self.tables[index].x1, self.tables[index].x2)
            self.plot_widget.canvas.draw()

    def switch_state(self):
        if self._atom.state == ProgramState.Modification and len(self._atom.lines) == 0:
            QMessageBox.critical(self, "Ошибка", "Некорректные данные для симплекс метода")
            return

        if self._atom.state == ProgramState.Modification:
            self.last_atom = self._atom
            self.lines_to_plot = []
            for i in range(len(self._atom.lines)):
                self.lines_to_plot.append(copy.deepcopy(self._atom.lines[i].line))

            self.compute_solution()
            self.combo_box.clear()

            for index in range(len(self.tables)):
                if isinstance(self.tables[index], Error):
                    QMessageBox.critical(self, "Ошибка", "Симплекс метод не имеет решения")
                    self.lines_to_plot = []
                    return

            for i in range(len(self.tables)):
                self.combo_box.addItem(f'Шаг {i + 1}')

            self.combo_box.currentIndexChanged.connect(self.on_combo_box_changed)
            self.table_widget.update_from_info(self.tables[0])
            self.plot_widget.ax.clear()
            self.plot_widget.gradient_color = 'r'
            self.plot_widget.selected_gradient = False
            self.plot_widget.draw_vector(*self.grad)
            self.plot_widget.draw_point(self.tables[0].x1, self.tables[0].x2)
            self.plot_widget.draw_lines(self.lines_to_plot)
            new_state = ProgramState.Viewing
            self.state_button.setText('Перейти к редактированию')
        else:
            self._atom = self.last_atom
            self.last_atom = None
            self.lines_to_plot = []
            new_state = ProgramState.Modification
            self.combo_box.clear()
            self.state_button.setText('Перейти к решению')
        self._atom.set_state(new_state)

    def save_state(self):
        """Saves the current table data and labels to a UTF-8 encoded text file."""
        if self._atom.state != ProgramState.Modification:
            QMessageBox.critical(self, "Ошибка", "Сохранение доступно только в режиме редактирования")
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getSaveFileName(self, "Сохранение таблицы", "", "Text Files (*.txt);;All Files (*)",
                                                   options=options)

        if not file_name:
            return

        if not file_name.lower().endswith(".txt"):
            file_name += ".txt"

        try:
            with open(file_name, 'w', encoding='utf-8') as f:
                # Save lines and gradient
                for line_entry in self._atom.lines:
                    f.write(",".join(map(str, line_entry.coeffs)) + "\n")
                f.write(",".join(map(str, self._atom.grad)) + "\n")

                # save limits
                f.write(str(self._atom.lim))

            QMessageBox.information(self, "Успех", f"Таблица сохранена: {file_name}")

        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Не удалось сохранить таблицу: {e}")

    def load_state(self):
        """Loads table data and labels from a UTF-8 encoded text file."""
        if self._atom.state != ProgramState.Modification:
            QMessageBox.critical(self, "Ошибка", "Загрузка доступна только в режиме редактирования")
            return

        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        file_name, _ = QFileDialog.getOpenFileName(self, "Загрузка таблицы", "", "Text Files (*.txt);;All Files (*)",
                                                   options=options)

        if not file_name:
            return

        try:
            with open(file_name, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # check file format (basic check - at least 2 lines are needed)
            if len(lines) < 2:
                QMessageBox.critical(self, "Ошибка", "Неверный формат файла")
                return

            # disconnect observers
            self.table_widget.table_widget.itemChanged.disconnect(self.table_widget.data_changed)

            # clear existing table and atom data
            while self.table_widget.table_widget.rowCount() > 0:
                self.table_widget.table_widget.removeRow(0)
            self._atom.lines = []
            self._atom.grad = []

            # load lines and gradient
            data_lines = lines[:-1]  # all lines except last 3 (labels and limits)
            num_lines = len(data_lines) - 1

            for row_idx, line in enumerate(data_lines):
                row_values = line.strip().split(",")
                if row_idx < num_lines:
                    # it's a line entry
                    if len(row_values) != 3:
                        raise ValueError(f"Неверное формат в строке {row_idx + 1}: {line.strip()}")
                    x1, x2, b = map(float, row_values)
                    self._atom.lines.append(LineEntry(x1, x2, b, shrink_line(table_row_to_vector(x1, x2, b, lim=self._atom.lim))))
                else:
                    # it's gradient
                    if len(row_values) != 3:
                        raise ValueError(f"Неверный формат градиента: {line.strip()}")
                    self._atom.grad = list(map(float, row_values))

            # load into table widget (for visual representation)
            for i in range(len(self._atom.lines)):
                row_idx = self.table_widget.table_widget.rowCount()
                self.table_widget.table_widget.insertRow(row_idx)

                data = self._atom.lines[i].coeffs
                for col in range(self.table_widget.table_widget.columnCount()):
                    item = QTableWidgetItem(str(data[col]) if is_float(data[col]) else '0')
                    item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                    self.table_widget.table_widget.setItem(row_idx, col, item)

            # gradient
            row_idx = self.table_widget.table_widget.rowCount()
            self.table_widget.table_widget.insertRow(row_idx)
            data = self._atom.grad
            for col in range(self.table_widget.table_widget.columnCount() - 1):
                item = QTableWidgetItem(str(data[col]) if is_float(data[col]) else '0')
                item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable | Qt.ItemIsEditable)
                self.table_widget.table_widget.setItem(row_idx, col, item)
            item = QTableWidgetItem('0')
            item.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
            self.table_widget.table_widget.setItem(row_idx, 2, item)

            # Load limits
            lims = int(lines[-1].strip())
            self.limit_slider.setValue(lims)  # set value
            self._atom.lim = lims  # save to variable

            self.table_widget.update_labels()

            # reconnect observers
            self.table_widget.table_widget.itemChanged.connect(self.table_widget.data_changed)

            QMessageBox.information(self, "Успех", "Таблица загружена")
            self._atom.notify_observers()

        except Exception as e:
            # reconnect observers
            self.table_widget.table_widget.itemChanged.connect(self.table_widget.data_changed)
            QMessageBox.critical(self, "Ошибка", f"Не удалось загрузить таблицу по причине: {e}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
