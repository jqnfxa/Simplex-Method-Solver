import copy
import sys
import configparser
from pathlib import Path

from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, \
    QToolBar, QComboBox, QMessageBox, QSlider, QTableWidgetItem, QFileDialog, QDialog, QLabel, QTextEdit
from PyQt5.QtCore import Qt

from atom import Atom, LineEntry
from equations import table_row_to_line, shrink_line, table_row_to_vector
from plot_widget import PlotWidget
from simplex import SimplexMethod, Error
from structs import ProgramState
from table_widget import TableWidget, is_float


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе")
        layout = QVBoxLayout()
        label = QLabel("PyQtSimplex v.2025\n\nРазработано в 2025 году\nАвтор: Борисов И.В.")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)
        self.setLayout(layout)


class HelpDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.text_edit = None
        self.setWindowTitle("Помощь")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setPlainText(self.get_help_text())
        layout.addWidget(self.text_edit)

        self.setLayout(layout)

    def get_help_text(self):
        return """
        Инструкция по использованию программы.

        1. **Режим редактирования (таблица)**
           - Добавление условий.
           Нажмите кнопку 'Добавить условие', чтобы добавить строку для ввода коэффициентов.
           По умолчанию будет добавлена строка со всеми 0
           
           - Удаление условий.
            Выберите строку и нажмите 'Удалить условие'
           
           - Ввод данных.
           Вводите коэффициенты уравнения (x1, x2, b) в соответствующие ячейки таблицы.  
           
           *Важно: Убедитесь, что вводите числа через '.'
           Пример верного ввода: '3.14'
           Пример неверного ввода: '3,14'
           
           - Градиент.
           В последней строке таблицы введите коэффициенты целевой функции (градиента).  
           Правый столбец (b) для градиента недоступен для редактирования.
           
           - Изменение масштаба.
           Используйте ползунок для изменения масштаба графика, при перемещении ползунка вправо масштаб будет увеличиваться,
           а при перемещении влево уменьшаться.
        
        2. **Режим редактирования (график)**
           - Добавление условий.
           При нажатии левой кнопки мыши ставится первая точка отрезка прямой.
           При отпускании левой кнопки мыши ставится вторая точка отрезка прямой и рисуется прямая.
           
           - Выделение прямой.
           Двойное нажатие левой кнопки мыши по прямой "выделяет" её, прямая будет отмечена другим цветом, 
           с этого момента её можно передвигать за точки или целиком.
           *Если прямая выделена, то её можно удалить нажатием на кнопку 'Удалить условие'
           
           - Отмена выделения прямой.
           Нажатие правой кнопки мыши отменяет выделение прямой.
           
           - Градиент прямой.
           Для изменения напрявления градиента прямой требуется сделать двойное нажатие левой кнопки мыши по концу градиента.
           
           - Градиент функции.
           Для изменения направления градиента функции требуется сделать двойное нажатие по концу градиента, 
           после чего он поменяет свой цвет и будут доступна возможность перемещать его.
           Для выхода из режима редактирования градиента требуется сделать нажатие правой кнопки мыши. 

        2. **Режим просмотра решения**
           - Переход к решению.
           Нажмите 'Перейти к решению'. Программа произведёт решение по симплекс-методу
           
           - Просмотр шагов.
           Используйте выпадающий список для выбора шага симплекс-метода и просмотра промежуточных результатов
           
           - График.
           На графике отображаются линии ограничений, вектор градиента и текущая точка решения
           *Значение функции для данной точки отображается в столбце 'b' строки 'f'
           
           - Возврат к редактированию.
           Нажмите 'Перейти к редактированию', чтобы изменить условия задачи

        3. **Сохранение и загрузка**
           - Сохранение.
           Нажмите 'Сохранить файл', чтобы сохранить текущие данные таблицы и масштаба в текстовый файл (.txt)
           Если расширение не указано явно, то файл будет дополнен суффиксом '.txt'
           
           - Загрузка.
           Нажмите 'Загрузить файл', чтобы загрузить данные из текстового файла

        4. **Ограничения**
           - Программа предназначена для решения задачи линейного программирования с двумя переменными F(x1, x2) -> max
           с условиями y ≥ 0
           
           F(x1,x2) = g1 · x1 + g2 · x2
           y: a1 · x1 + a2 · x2 + b ≥ 0 

        5. **Ошибки**
            - Если данные введены некорректно (например, не числа в ячейках), программа выдаст сообщение об ошибке
            - Если симплекс-метод не имеет решения, программа также сообщит об этом

        6. **Помощь и О программе**
           - Доступны кнопки "Помощь" (эта инструкция) и "О программе" (информация о разработчике)

        Описание алгоритма формализации прямой.
        Пусть даны точки (x1, y1), (x2, y2). 
        Требуется построить уравнение прямой по этим точкам вида:
        ```
        a · x + b · y + c ≥ 0
        ```
        Градиент: (-(y2 - y1), (x2 - x1)) 
        ```
        a = y1 − y2
        b = x2 − x1
        c = x1 · y2 − x2 · y1
        n = max(1.0, max(|a|, |b|))
        ```
        Окончательные значения (нормирование):
        ```
        a = a / n
        b = b / n
        c = c / n
        ```
        """


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.grad = None
        self.lines_to_plot = None
        self.setWindowTitle("PyQtSimplex v.2025")
        self.config = configparser.ConfigParser()
        self.config_path = "config.cfg"
        self.load_config()

        # fullscreen mode
        screen_geometry = QApplication.screens()[0].availableGeometry()
        width = screen_geometry.width()
        height = screen_geometry.height()
        self.setGeometry(0, 0, width, height)

        # modifiable data
        self._atom = Atom(ProgramState.Modification, [], [0, 1, 0], self.config.getint('settings', 'default_scale'))

        # widgets
        self.table_widget = TableWidget(self._atom)
        self.plot_widget = PlotWidget(self._atom)
        self.last_atom = None
        self.tables = None
        self.lines = None

        # tolerance
        self.plot_widget.pptol = self.config.getfloat('settings', 'point_tolerance')
        self.plot_widget.pltol = self.config.getfloat('settings', 'line_tolerance')

        # colors
        self.plot_widget.default_line_color = self.config.get('settings', 'default_line_color')
        self.plot_widget.default_point_color = self.config.get('settings', 'default_point_color')
        self.plot_widget.selected_line_color = self.config.get('settings', 'selected_line_color')
        self.plot_widget.gradient_line_color = self.config.get('settings', 'gradient_line_color')
        self.plot_widget.gradient_function_color = self.config.get('settings', 'gradient_function_color')
        self.plot_widget.optimal_point_color = self.config.get('settings', 'optimal_point_color')
        self.plot_widget.update()

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

        # save/load buttons
        self.save_button = QPushButton('Сохранить файл')
        self.save_button.clicked.connect(self.save_state)  # type: ignore
        self.load_button = QPushButton('Загрузить файл')
        self.load_button.clicked.connect(self.load_state)  # type: ignore

        # slider for limits
        self.limit_slider = QSlider(Qt.Horizontal)
        self.limit_slider.setMinimum(self.config.getint('settings', 'min_scale'))
        self.limit_slider.setMaximum(self.config.getint('settings', 'max_scale'))
        self.limit_slider.setValue(self.config.getint('settings', 'default_scale'))
        self.plot_widget.min_scale = self.config.getint('settings', 'min_scale')
        self.limit_slider.valueChanged.connect(self.update_limits)  # type: ignore

        # help/about buttons
        self.help_button = QPushButton('Помощь')
        self.help_button.clicked.connect(self.show_help)  # type: ignore
        self.about_button = QPushButton('О программе')
        self.about_button.clicked.connect(self.show_about)  # type: ignore

        # toolbar with buttons
        toolbar = QToolBar()
        toolbar.addWidget(self.combo_box)
        toolbar.addWidget(self.state_button)
        toolbar.addWidget(self.insert_row_button)
        toolbar.addWidget(self.remove_row_button)
        toolbar.addWidget(self.save_button)
        toolbar.addWidget(self.load_button)
        toolbar.addWidget(self.help_button)
        toolbar.addWidget(self.about_button)
        toolbar.addWidget(self.limit_slider)
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

    def load_config(self):
        config_file = Path(self.config_path)
        if config_file.is_file():
            self.config.read(self.config_path)
        else:
            self.config['settings'] = {
                'point_tolerance': '0.15',
                'line_tolerance': '0.15',
                'min_scale': '10',
                'max_scale': '100',
                'default_scale': '10',
                'default_line_color': 'blue',
                'default_point_color': 'red',
                'selected_line_color': 'green',
                'gradient_line_color': 'red',
                'gradient_function_color': 'blue',
                'optimal_point_color': 'red',
            }
            with open(self.config_path, 'w') as configfile:
                self.config.write(configfile)

        if 'settings' not in self.config:
            self.config['settings'] = {}
        for option in ['point_tolerance', 'line_tolerance', 'min_scale', 'max_scale', 'default_scale', 'default_line_color',
                       'default_point_color', 'selected_line_color', 'gradient_line_color',
                       'gradient_function_color', 'optimal_point_color']:
            if option not in self.config['settings']:
                # Provide defaults if a setting is missing, prevents crashing
                defaults = {
                    'point_tolerance': '0.15',
                    'line_tolerance': '0.15',
                    'min_scale': '10',
                    'max_scale': '100',
                    'default_scale': '10',
                    'default_line_color': 'blue',
                    'default_point_color': 'red',
                    'selected_line_color': 'green',
                    'gradient_line_color': 'red',
                    'gradient_function_color': 'blue',
                    'optimal_point_color': 'red',
                }
                self.config['settings'][option] = defaults[option]

    def update_limits(self, value):
        self._atom.lim = value
        self.plot_widget.update()

    def show_help(self):
        dialog = HelpDialog(self)
        dialog.exec_()

    def show_about(self):
        dialog = AboutDialog()
        dialog.exec_()

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
            self.plot_widget.gradient_color = self.plot_widget.gradient_function_color
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

            new_lines = []
            new_grad = []

            # load lines and gradient
            data_lines = lines[:-1]  # all lines except last 3 (labels and limits)
            num_lines = len(data_lines) - 1

            for row_idx, line in enumerate(data_lines):
                row_values = line.strip().split(",")
                if row_idx < num_lines:
                    # it's a line entry
                    if len(row_values) != 3:
                        raise ValueError(f"Неверный формат в строке {row_idx + 1}: {line.strip()}")
                    x1, x2, b = map(float, row_values)
                    new_lines.append(LineEntry(x1, x2, b, shrink_line(table_row_to_vector(x1, x2, b, lim=self._atom.lim))))
                else:
                    # it's gradient
                    if len(row_values) != 3:
                        raise ValueError(f"Неверный формат градиента: {line.strip()}")
                    new_grad = list(map(float, row_values))

            # clear existing table and atom data
            while self.table_widget.table_widget.rowCount() > 0:
                self.table_widget.table_widget.removeRow(0)

            self._atom.lines = new_lines
            self._atom.grad = new_grad

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
