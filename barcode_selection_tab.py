import tkinter as tk
from tkinter import ttk


class BarcodeSelectionTab(ttk.Frame):
    """
    Вкладка для отображения всех доступных штрих-кодов с чекбоксами для выбора.
    """

    def __init__(self, parent, app, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.app = app  # Ссылка на основной класс приложения

        # Словарь для хранения переменных чекбоксов {имя_файла: tk.IntVar}
        self.checkbox_vars = {}

        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты на вкладке."""
        # Фрейм для кнопки "Добавить"
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        add_button = ttk.Button(
            bottom_frame,
            text="Добавить выбранные в список",
            command=self.add_selected_to_main_list,
        )
        add_button.pack()

        # --- Фрейм с прокруткой для списка чекбоксов ---
        main_frame = ttk.Frame(self)
        main_frame.pack(side="top", fill="both", expand=True, padx=10, pady=(10, 0))

        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)

        self.scrollable_frame.bind(
            "<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def populate_barcodes(self, barcode_files):
        """Заполняет фрейм чекбоксами на основе списка файлов."""
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()
        self.checkbox_vars.clear()

        for filename in barcode_files:
            var = tk.IntVar()
            cb = ttk.Checkbutton(self.scrollable_frame, text=filename, variable=var)
            cb.pack(anchor="w", padx=10, pady=2, fill="x")
            self.checkbox_vars[filename] = var

    def add_selected_to_main_list(self):
        """Добавляет выбранные штрих-коды в основной список генерации."""
        self.app.add_barcodes_from_selection_tab(self.checkbox_vars)
        # self.app.switch_to_main_tab() # Этот вызов теперь находится внутри add_barcodes_from_selection_tab
