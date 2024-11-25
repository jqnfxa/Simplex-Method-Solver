import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.pyplot as plt
import sys  # Для завершения программы

class SimplexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Simplex Application")

        # Добавляем обработчик закрытия окна
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Левый фрейм для таблицы
        self.left_frame = ttk.Frame(root)
        self.left_frame.grid(row=0, column=0, padx=10, pady=10, sticky="ns")
        
        # Таблица
        self.table = ttk.Treeview(self.left_frame, columns=("x1", "x2", "-b"), show="headings", height=10)
        self.table.heading("x1", text="x1")
        self.table.heading("x2", text="x2")
        self.table.heading("-b", text="-b")
        self.table.pack()

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

    def add_row(self):
        self.table.insert("", "end", values=("0.0", "0.0", "0.0"))

    def delete_row(self):
        selected_item = self.table.selection()
        if selected_item:
            self.table.delete(selected_item)

    def on_click(self, event):
        if event.xdata is not None and event.ydata is not None:
            self.line_start = (event.xdata, event.ydata)

    def on_release(self, event):
        if event.xdata is not None and event.ydata is not None:
            self.line_end = (event.xdata, event.ydata)
            if self.line_start and self.line_end:
                x_values = [self.line_start[0], self.line_end[0]]
                y_values = [self.line_start[1], self.line_end[1]]
                self.ax.plot(x_values, y_values, "r-")
                self.canvas.draw()
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

    def on_closing(self):
        """Функция для обработки закрытия окна."""
        plt.close("all")  # Закрыть все фигуры matplotlib
        self.root.destroy()  # Закрыть главное окно Tkinter
        sys.exit(0)  # Полностью завершить программу

if __name__ == "__main__":
    root = tk.Tk()
    app = SimplexApp(root)
    root.mainloop()
