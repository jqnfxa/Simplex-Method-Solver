import copy
import sys

from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QToolBar, QComboBox, QMessageBox
from PyQt5.QtCore import Qt

from atom import Atom
from equations import table_row_to_line
from plot_widget import PlotWidget
from simplex import SimplexMethod, Info, Error
from structs import ProgramState
from table_widget import TableWidget


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.lines_to_plot = None
        self.setWindowTitle("QtSimplex v.2025")

        # fullscreen mode
        screen_geometry = QApplication.screens()[0].availableGeometry()
        width = screen_geometry.width()
        height = screen_geometry.height()
        self.setGeometry(0, 0, width, height)

        # modifiable data
        self._atom = Atom(ProgramState.Modification, [], [], [20, 20])

        # widgets
        self.table_widget = TableWidget(self._atom)
        self.plot_widget = PlotWidget(self._atom)
        self.last_atom = None
        self.tables = None
        self.lines = None

        # reactive reaction
        self._atom.add_observer(self)

        # solution combo box
        self.combo_box = QComboBox()

        self.state_button = QPushButton('Перейти к решению')
        self.state_button.clicked.connect(self.switch_state)

        self.insert_row_button = QPushButton('Добавить условие')
        self.insert_row_button.clicked.connect(self.table_widget.insert_row)

        self.remove_row_button = QPushButton('Удалить условие')
        self.remove_row_button.clicked.connect(self.table_widget.remove_row)
        self.remove_row_button.clicked.connect(self.plot_widget.remove_line)

        # toolbar with buttons
        toolbar = QToolBar()
        toolbar.addWidget(self.combo_box)
        toolbar.addWidget(self.state_button)
        toolbar.addWidget(self.insert_row_button)
        toolbar.addWidget(self.remove_row_button)
        self.addToolBar(Qt.TopToolBarArea, toolbar)

        main_layout = QHBoxLayout()
        main_layout.addWidget(self.table_widget, 2)
        main_layout.addWidget(self.plot_widget, 8)

        container_layout = QVBoxLayout()
        container_layout.addLayout(main_layout)

        container = QWidget()
        container.setLayout(container_layout)
        self.setCentralWidget(container)

    def update(self):
        self.table_widget.update()
        self.plot_widget.update()

    def compute_solution(self):
        y = []
        for row in self._atom.lines:
            y.append(list(map(float, row[:3])))
        c = copy.deepcopy(self._atom.grad)[:-1]
        self.tables = SimplexMethod(y, c).get_solution()
        self.lines = []
        for line in y:
            self.lines.append(table_row_to_line(*line, self._atom.lims))

    def on_combo_box_changed(self, index):
        if index != -1:
            self.table_widget.update_from_info(self.tables[index])
            self.plot_widget.draw_lines(self.lines_to_plot)
            self.plot_widget.draw_point(self.tables[index].x1, self.tables[index].x2)

    def switch_state(self):
        if self._atom.state == ProgramState.Modification and len(self._atom.lines) == 0:
            QMessageBox.critical(self, "Ошибка", "Некорректные данные для симплекс метода")
            return

        if self._atom.state == ProgramState.Modification:
            self.last_atom = self._atom
            self.lines_to_plot = []
            for i in range(len(self._atom.lines)):
                self.lines_to_plot.append(copy.deepcopy(self._atom.lines[i][-1]))

            self.compute_solution()
            self.combo_box.clear()

            for index in range(len(self.tables)):
                if type(self.tables[index]) == Error:
                    QMessageBox.critical(self, "Ошибка", "Симплекс метод не имеет решения")
                    self.lines_to_plot = []
                    return

            for i in range(len(self.tables)):
                self.combo_box.addItem(f'Шаг {i + 1}')

            self.combo_box.currentIndexChanged.connect(self.on_combo_box_changed)
            self.table_widget.update_from_info(self.tables[0])
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


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
