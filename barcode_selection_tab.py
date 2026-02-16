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
        # --- Нижний фрейм для кнопок управления ---
        bottom_frame = ttk.Frame(self)
        bottom_frame.pack(side="bottom", fill="x", pady=10, padx=10)

        # Фрейм для кнопок "Выбрать все" / "Снять все"
        selection_buttons_frame = ttk.Frame(bottom_frame)
        selection_buttons_frame.pack(pady=(0, 5))

        select_all_button = ttk.Button(
            selection_buttons_frame,
            text="Выбрать все",
            command=self.select_all,
        )
        select_all_button.pack(side="left", padx=5)

        deselect_all_button = ttk.Button(
            selection_buttons_frame,
            text="Снять все",
            command=self.deselect_all,
        )
        deselect_all_button.pack(side="left", padx=5)

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

        # --- Привязка событий прокрутки колеса мыши ---
        # Это ключевой момент, которого не хватало.
        # Мы привязываем событие прокрутки к canvas, чтобы он мог скроллиться.
        canvas.bind_all(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )
        # Также привяжем к самому фрейму, чтобы прокрутка работала, когда курсор над элементами
        self.scrollable_frame.bind_all(
            "<MouseWheel>",
            lambda event: canvas.yview_scroll(int(-1 * (event.delta / 120)), "units"),
        )

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

    def select_all(self):
        """Отмечает все чекбоксы в списке."""
        for var in self.checkbox_vars.values():
            var.set(1)

    def deselect_all(self):
        """Снимает отметки со всех чекбоксов в списке."""
        for var in self.checkbox_vars.values():
            var.set(0)
