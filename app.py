import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import sys

class SimplexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simplex Application")

        # Добавляем обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Словарь для связи строк таблицы с линиями на графике
        self.line_map = {}

        self.vector_map = {}  # Словарь для хранения векторов

        # Левый фрейм для таблицы
        self.left_frame = ttk.Frame(root)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")

        # Таблица с прокруткой
        self.table_frame = ttk.Frame(self.left_frame)
        self.table_frame.pack(fill="both", expand=True)

        # Создание таблицы
        self.table = ttk.Treeview(
            self.table_frame,
            columns=("x1", "x2", "-b"),
            show="headings",  # Отображаем только колонки, убираем "основную колонку"
            height=10,
        )
        # Добавляем названия столбцов
        self.table["show"] = ("tree", "headings")  # Включаем колонку для строк
        self.table.heading("#0", text="Строка", anchor="w")  # Колонка строк
        self.table.column("#0", width=60, anchor="w")  # Размер и выравнивание
        self.table.heading("x1", text="x1", anchor="center")
        self.table.heading("x2", text="x2", anchor="center")
        self.table.heading("-b", text="-b", anchor="center")
        self.table.column("x1", width=60, anchor="center")
        self.table.column("x2", width=60, anchor="center")
        self.table.column("-b", width=60, anchor="center")

        # Вертикальный скролл
        self.scrollbar = ttk.Scrollbar(self.table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.table.pack(fill="both", expand=True)

        # Кнопки для добавления/удаления строк
        self.add_button = ttk.Button(self.left_frame, text="Добавить", command=self.add_row)
        self.add_button.pack(pady=5)
        self.delete_button = ttk.Button(self.left_frame, text="Удалить", command=self.delete_row)
        self.delete_button.pack(pady=5)

        # Правый фрейм для графика
        self.right_frame = ttk.Frame(root)
        self.right_frame.grid(row=0, column=1, padx=10, pady=10)

        # Матплотлиб график
        self.fig, self.ax = plt.subplots(figsize=(5, 4))
        self.ax.set_title("График")
        self.ax.grid(True)

        # Устанавливаем фиксированные границы осей
        self.ax.set_xlim(0, 20)  # Установите желаемые пределы для X-оси
        self.ax.set_ylim(0, 20)  # Установите желаемые пределы для Y-оси

        self.canvas = FigureCanvasTkAgg(self.fig, master=self.right_frame)
        self.canvas.get_tk_widget().pack()
        self.canvas.mpl_connect("button_press_event", self.on_click)
        self.canvas.mpl_connect("button_release_event", self.on_release)

        # Переменные для линии
        self.line_start = None
        self.line_end = None
        self.temp_line = None  # Временная линия для отображения

        # Подключение события движения мыши
        self.canvas.mpl_connect("motion_notify_event", self.on_motion)

        # Нижняя панель кнопок
        self.bottom_frame = ttk.Frame(root)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, pady=10)

        # Переменная состояния кнопок
        self.active_button = tk.StringVar(value="")

        # Кнопки переключатели
        self.condition_button = ttk.Button(self.bottom_frame, text="Условие", command=self.toggle_condition)
        self.condition_button.grid(row=0, column=0, padx=5)

        self.solution_button = ttk.Button(self.bottom_frame, text="Решение", command=self.toggle_solution)
        self.solution_button.grid(row=0, column=1, padx=5)

        self.step_var = tk.StringVar(value="Шаг 1")
        self.step_menu = ttk.Combobox(self.bottom_frame, textvariable=self.step_var, values=["Шаг 1", "Шаг 2", "Шаг 3"])
        self.step_menu.grid(row=0, column=2, padx=5)

        # Добавляем элементы для изменения масштаба графика
        self.scale_var = tk.DoubleVar(value=20)  # Начальное значение масштаба
        self.scale_label = ttk.Label(self.bottom_frame, text="Масштаб:")
        self.scale_label.grid(row=0, column=3, padx=5)
        self.scale_entry = ttk.Entry(self.bottom_frame, textvariable=self.scale_var, width=5)
        self.scale_entry.grid(row=0, column=4, padx=5)
        self.scale_button = ttk.Button(self.bottom_frame, text="Применить", command=self.update_scale)
        self.scale_button.grid(row=0, column=5, padx=5)

        # Словарь для хранения текущей выделенной линии
        self.selected_line = None

        # Инициализация строки
        self.set_func_minimizate()
        self.initialize_table()

        # Привязка событий для редактирования
        self.table.bind("<Double-1>", self.edit_cell)

        # Устанавливаем возможность выделения строк в таблице
        self.table.bind("<<TreeviewSelect>>", self.on_table_select)

        # Привязка события клавиши Delete к корневому окну
        self.root.bind("<Delete>", lambda *t: self.delete_row())
        
        # Подключение события клика по графику
        self.canvas.mpl_connect("pick_event", self.on_line_click)

    def get_x_y_for_graph(self, point1, point2):
        x1, y1 = point1
        x2, y2 = point2

        # Пределы графика
        x_min, x_max = self.ax.get_xlim()
        y_min, y_max = self.ax.get_ylim()

        # Уравнение прямой: y = kx + b
        if x1 != x2:  # Если линия не вертикальная
            k = (y2 - y1) / (x2 - x1)  # Наклон
            b = y1 - k * x1  # Сдвиг

            # Вычисление точек пересечения с границами графика
            x_vals = [x_min, x_max]
            y_vals = [k * x_min + b, k * x_max + b]

            # Обрезаем линию, если она выходит за пределы по Y
            if k == 0:
                ...
            elif y_vals[1] < y_min or y_vals[1] > y_max:
                y_vals[1] = y_min if k < 0 else y_max
                x_vals[1] = ((20 if k > 0 else 0) - b) / k
            elif y_vals[0] < y_min or y_vals[0] > y_max:
                y_vals[0] = y_min if k > 0 else y_max
                x_vals[0] = ((20 if k < 0 else 0) - b) / k
                
        else:  # Если линия вертикальная
            x_vals = [x1, x1]
            y_vals = [y_min, y_max]

        return x_vals, y_vals
    
    def set_func_minimizate(self, x1=1.0, x2=1.0, neg_b=.0):
        if (len(self.table.get_children()) == 0):
            row_name = f"c"  # Название строки
            self.table.insert("", "end", text=row_name, values=(str(x1), str(x2), str(neg_b)))
            return 
        self.table.item(self.table.get_children()[0], values=(str(x1), str(x2), str(neg_b)))

    def initialize_table(self):
        """Инициализация таблицы несколькими строками."""
        for i in range(1):  # Добавляем 5 строк по умолчанию
            self.add_row()

    def add_row(self, x1=1.0, x2=-1.0, neg_b=3.0):
        """Добавление строки в таблицу и создание линии на графике."""
        row_name = f"y{len(self.table.get_children())}"  # Название строки
        item_id = self.table.insert("", "end", text=row_name, values=(str(x1), str(x2), str(neg_b)))
        
        # Создаем соответствующую линию на графике
        self.create_line_for_row(item_id, x1, x2, neg_b)
    
    def delete_row(self):
        """Удаление выбранной строки из таблицы и линии с графика."""
        selected_items = self.table.selection()
        first_item = self.table.get_children()[0]  # Первая строка таблицы

        # Убираем выделение текущей линии
        if self.selected_line:
            self.selected_line.set_color("b")
            self.selected_line = None

        for item_id in selected_items:
            if item_id == first_item:
                continue
            
            # Удаляем линию с графика
            self.delete_line_for_row(item_id)
            # Удаляем строку из таблицы
            self.table.delete(item_id)

        self.update_row_names()

    def update_row_names(self):
        """Обновление названий строк после удаления."""
        for index, item in enumerate(self.table.get_children()[1:]):
            self.table.item(item, text=f"y{index + 1}")  # Обновляем текст строки

    def edit_cell(self, event):
        """Редактирование значения в ячейке таблицы с обновлением линии."""
        item_id = self.table.identify_row(event.y)
        column_id = self.table.identify_column(event.x)

        if not item_id or not column_id:
            return

        column_index = int(column_id.strip("#")) - 1
        current_value = self.table.item(item_id)["values"][column_index]

        # Создаем виджет ввода
        entry = tk.Entry(self.table)
        entry.insert(0, current_value)
        entry.place(x=event.x_root - self.table.winfo_rootx(),
                    y=event.y_root - self.table.winfo_rooty(),
                    width=100, height=20)

        def save_edit(event):
            new_value = entry.get()
            if self.is_valid_value(new_value):  # Проверяем валидность
                values = list(self.table.item(item_id)["values"])
                values[column_index] = new_value
                self.table.item(item_id, values=values)
                self.update_line_for_row(item_id, values)
            entry.destroy()

        def cancel_edit(event):
            entry.destroy()

        entry.bind("<Return>", save_edit)
        entry.bind("<FocusOut>", cancel_edit)
        entry.focus_set()

    def is_valid_value(self, value):
        """Проверка валидности вводимого значения."""
        try:
            float(value)  # Разрешены числа с плавающей точкой
            return True
        except ValueError:
            return False
    
    def create_line_for_row(self, item_id, x1, x2, neg_b):
        """Создание линии на графике для строки таблицы."""
        # Ваша логика преобразования данных из таблицы в параметры линии
        # Например:
        x_vals = [0, 20]  # Пример координат X
        y_vals = [0, 20]  # Пример координат Y

        # Рисуем линию
        line, = self.ax.plot(x_vals, y_vals, label=item_id, color="b", picker=True, pickradius=5)
        self.line_map[item_id] = line  # Сохраняем линию в словарь
        self.update_line_for_row(item_id, [x1, x2, neg_b])

    def update_line_for_row(self, item_id, values):
        """Обновление линии на графике при изменении данных строки."""
        if item_id not in self.line_map:
            return
        
        values = [*map(float, values)]
        values[2] = -1 * values[2]
        if values[0] == 0 and values[1] == 0:
            x_vals, y_vals = self.get_x_y_for_graph((0, 0), (0, 0))
        elif values[0] == 0:
            x_vals, y_vals = self.get_x_y_for_graph((0, values[2] / values[1]), (1, values[2] / values[1]))
        elif values[1] == 0:
            x_vals, y_vals = self.get_x_y_for_graph((values[2] / values[0], 1), (values[2] / values[0], 0))
        else:
            x_vals, y_vals = self.get_x_y_for_graph((0, values[2] / values[1]), (values[2] / values[0], 0))

        # Обновляем линию
        line = self.line_map[item_id]
        line.set_data(x_vals, y_vals)

        # Обновляем вектор
        self.update_vector_for_row(item_id, x_vals, y_vals, values)

        self.canvas.draw()

    def delete_line_for_row(self, item_id):
        """Удаление линии с графика для строки таблицы."""
        if item_id in self.line_map:
            line = self.line_map[item_id]
            line.remove()  # Удаляем линию с графика
            del self.line_map[item_id]  # Удаляем из словаря
            if line == self.selected_line:
                self.selected_line = None
        
        if item_id in self.vector_map:
            vec = self.vector_map[item_id]
            vec.remove()  # Удаляем вектор с графика
            del self.vector_map[item_id]  # Удаляем из словаря

        self.canvas.draw()
    
    def update_vector_for_row(self, item_id, x_vals, y_vals, values):
        """Добавление или обновление вектора для строки таблицы."""
        # Середина линии
        x_mid = (x_vals[0] + x_vals[1]) / 2
        y_mid = (y_vals[0] + y_vals[1]) / 2

        # Направление вектора из x1, x2
        x_dir, y_dir = values[0], values[1]

        # Нормализуем длину вектора до 0.1 от масштаба
        scale = 0.05 * (self.ax.get_xlim()[1] - self.ax.get_xlim()[0])
        length = (x_dir**2 + y_dir**2)**0.5
        if length > 0:
            x_dir, y_dir = (x_dir / length) * scale, (y_dir / length) * scale

        # Удаляем старый вектор, если он есть
        if item_id in self.vector_map:
            vec = self.vector_map[item_id]
            vec.remove()

        # Добавляем новый вектор
        vec = self.ax.quiver(x_mid, y_mid, x_dir, y_dir, angles='xy', scale_units='xy', scale=1, color='b')
        self.vector_map[item_id] = vec
    
    def on_line_click(self, event):
        """Обработка клика на линии."""
        line = event.artist  # Получаем объект линии
        item_id = None

        # Ищем соответствующую строку в таблице
        for key, value in self.line_map.items():
            if value == line:
                item_id = key
                break

        if item_id:
            is_highlight_line = line == self.selected_line
            self.highlight_line(line)  # Выделяем линию
            self.highlight_row(item_id)  # Выделяем строку таблицы
            
            if not is_highlight_line:
                return

            # Меняем все значения в строке на отрицательные
            values = self.table.item(item_id)["values"]
            new_values = [-float(value) for value in values]  # Меняем на отрицательные значения
            self.table.item(item_id, values=new_values)  # Обновляем строку в таблице

            # Обновляем линию на графике с новыми значениями
            self.update_line_for_row(item_id, new_values)
    
    def on_table_select(self, event):
        """Обработка выделения строки в таблице."""
        selected_items = self.table.selection()

        # Убираем выделение с текущей линии
        if self.selected_line:
            self.selected_line.set_color("b")
            self.selected_line = None

        # Обрабатываем первую выбранную строку
        if selected_items:
            item_id = selected_items[0]
            if item_id in self.line_map:
                line = self.line_map[item_id]
                self.highlight_line(line)

    def highlight_line(self, line):
        """Выделение линии и связанного с ней вектора."""
        # Сбрасываем выделение текущей линии
        if self.selected_line:
            self.selected_line.set_color("b")
            # Сбрасываем цвет для связанного вектора
            for item_id, existing_line in self.line_map.items():
                if existing_line == self.selected_line and item_id in self.vector_map:
                    self.vector_map[item_id].set_color("b")

        # Устанавливаем новую выделенную линию
        self.selected_line = line
        line.set_color("g")
        
        # Выделяем цветом связанный вектор
        for item_id, existing_line in self.line_map.items():
            if existing_line == line and item_id in self.vector_map:
                self.vector_map[item_id].set_color("g")
        
        self.canvas.draw()

    def highlight_row(self, item_id):
        """Выделение строки таблицы."""
        self.table.selection_set(item_id)
        self.table.see(item_id)  # Прокрутка таблицы к строке, если она скрыта

    def on_click(self, event):
        """Обработка нажатия мыши."""
        if event.xdata is None or event.ydata is None:
            return

        self.line_start = (event.xdata, event.ydata)
        # Инициализируем временную линию
        self.temp_line, = self.ax.plot([event.xdata, event.xdata],
                                    [event.ydata, event.ydata],
                                    linestyle="--", color="gray")
        self.canvas.draw()

    def on_motion(self, event):
        """Обработка движения мыши с зажатой кнопкой."""
        if self.line_start and event.xdata is not None and event.ydata is not None:
            x1, y1 = self.line_start
            x2, y2 = event.xdata, event.ydata

            if self.temp_line is None:
                return

            # Обновляем временную линию
            self.temp_line.set_data([x1, x2], [y1, y2])
            self.canvas.draw()

    def on_release(self, event):
        """Обработка отпускания мыши."""
        if event.xdata is None or event.ydata is None:
            return

        self.line_end = (event.xdata, event.ydata)
        if self.line_start is None or self.line_end is None:
            return

        # Удаляем временную линию
        if self.temp_line:
            self.temp_line.remove()
            self.temp_line = None
        
        # Добавляем постоянную линию
        x1, y1 = self.line_start
        x2, y2 = self.line_end

        k = (y2 - y1) / (x2 - x1)  # Наклон
        b = y1 - k * x1  # Сдвиг

        if k != k:
            return

        self.add_row(k, -1, b)
        self.line_start = None
        self.line_end = None

    def toggle_condition(self):
        """Обработчик кнопки 'Условие'."""
        if self.active_button.get() != "condition":
            self.active_button.set("condition")
            self.condition_button.state(["pressed"])
            self.solution_button.state(["!pressed"])
        else:
            self.active_button.set("")
            self.condition_button.state(["!pressed"])

    def toggle_solution(self):
        """Обработчик кнопки 'Решение'."""
        if self.active_button.get() != "solution":
            self.active_button.set("solution")
            self.solution_button.state(["pressed"])
            self.condition_button.state(["!pressed"])
        else:
            self.active_button.set("")
            self.solution_button.state(["!pressed"])
    
    def update_scale(self):
        """Обновляет границы осей графика в соответствии с заданным масштабом."""
        try:
            max_value = float(self.scale_var.get())  # Получаем новое значение масштаба
            if max_value <= 0:
                raise ValueError("Масштаб должен быть положительным числом.")
            self.ax.set_xlim(0, max_value)
            self.ax.set_ylim(0, max_value)
            self.canvas.draw()
        except ValueError as e:
            print(f"Ошибка: {e}")

    def on_closing(self):
        plt.close("all")
        self.root.destroy()
        sys.exit(0)

if __name__ == "__main__":
    root = tk.Tk()
    app = SimplexApp(root)
    root.mainloop()
