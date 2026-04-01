import os
import tempfile
import tkinter as tk
from tkinter import messagebox, ttk

import fitz  # PyMuPDF
import win32api
from PIL import Image, ImageTk

import pdf_generator


class RibbonPrintTab(ttk.Frame):
    """
    Вкладка для выбора PDF-файлов, их объединения и отправки на ленточный принтер.
    """

    def __init__(self, parent, app, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.app = app  # Ссылка на основной класс приложения

        self.all_pdf_files = []
        self.selected_for_printing = {}  # {имя_файла: количество}
        self.preview_image = None  # Ссылка на изображение для предпросмотра

        self.create_widgets()

    def create_widgets(self):
        """Создает виджеты на вкладке."""
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="y", expand=False, padx=(0, 10), pady=10)

        # --- 1. Фрейм выбора ---
        selection_frame = ttk.LabelFrame(
            left_panel, text="Шаг 1: Выбор PDF со штрих-кодом", padding=(10, 5)
        )
        selection_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(selection_frame, text="PDF-файл:").grid(
            row=0, column=0, padx=(0, 5), sticky="w"
        )
        self.pdf_selector = ttk.Combobox(
            selection_frame, state="normal", width=30, height=20
        )
        self.pdf_selector.grid(row=0, column=1, padx=5, sticky="ew")
        self.pdf_selector.bind(
            "<<ComboboxSelected>>", self.update_preview_from_combobox
        )
        self.pdf_selector.bind("<KeyRelease>", self.filter_pdfs)

        ttk.Label(selection_frame, text="Кол-во:").grid(
            row=0, column=2, padx=(10, 5), sticky="w"
        )
        self.quantity_input = ttk.Entry(selection_frame, width=10)
        self.quantity_input.insert(0, "1")
        self.quantity_input.grid(row=0, column=3, padx=5, sticky="w")

        add_button = ttk.Button(
            selection_frame,
            text="Добавить",
            command=self.add_to_list,
            style="Success.TButton",
        )
        add_button.grid(row=0, column=4, padx=(5, 0))
        selection_frame.columnconfigure(1, weight=1)

        # --- 2. Список для печати ---
        list_frame = ttk.LabelFrame(
            left_panel, text="Шаг 2: Список для печати", padding=(10, 5)
        )
        list_frame.pack(fill="both", expand=True, pady=5)

        columns = ("filename", "quantity", "delete")
        self.print_list_view = ttk.Treeview(
            list_frame, columns=columns, show="headings"
        )
        self.print_list_view.heading("filename", text="Имя файла")
        self.print_list_view.heading("quantity", text="Количество")
        self.print_list_view.heading("delete", text="Удалить")
        self.print_list_view.column("quantity", width=100, anchor="center")
        self.print_list_view.column("delete", width=60, anchor="center")

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.print_list_view.yview
        )
        self.print_list_view.configure(yscrollcommand=scrollbar.set)
        self.print_list_view.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Привязываем событие двойного клика для редактирования
        self.print_list_view.bind("<Double-1>", self.edit_list_item)
        # Обновляем предпросмотр при выборе из списка
        self.print_list_view.bind("<<TreeviewSelect>>", self.update_preview_from_list)
        # Привязываем событие клика для удаления
        self.print_list_view.bind("<ButtonPress-1>", self.handle_list_click)

        # --- 3. Кнопки управления ---
        clear_button = ttk.Button(
            left_panel,
            text="Убрать все",
            command=self.clear_list,
            style="Danger.TButton",
        )
        clear_button.pack(pady=5)

        print_button = ttk.Button(
            left_panel,
            text="Объединить и напечатать",
            command=self.process_ribbon_printing,
            style="Success.TButton",
        )
        print_button.pack(pady=(0, 5))

        # --- 4. Фрейм для предпросмотра ---
        preview_frame = ttk.LabelFrame(right_panel, text="Предпросмотр", padding=10)
        preview_frame.pack(fill="both", expand=True)

        self.preview_label = ttk.Label(
            preview_frame,
            text="Выберите PDF-файл",
            background=self.app.FRAME_BG,
            anchor="center",
        )
        self.preview_label.pack(fill="both", expand=True)

    def load_pdf_list(self):
        """Загружает список PDF-файлов из указанной директории."""
        self.clear_list(silent=True)
        self.pdf_selector.set("")
        pdf_dir = self.app.pdf_source_dir

        if not os.path.isdir(pdf_dir):
            self.all_pdf_files = []
            self.pdf_selector["values"] = []
            self.app.update_status("Папка с PDF не найдена. Укажите путь в Настройках.")
            return

        self.all_pdf_files = sorted(
            [f for f in os.listdir(pdf_dir) if f.lower().endswith(".pdf")]
        )
        self.pdf_selector["values"] = self.all_pdf_files
        if self.all_pdf_files:
            self.pdf_selector.current(0)
            self.show_pdf_preview(self.pdf_selector.get())
            self.app.update_status(f"Найдено {len(self.all_pdf_files)} PDF файлов.")
        else:
            self.app.update_status("В папке с PDF не найдено файлов.")
            self.show_pdf_preview(None)

    def filter_pdfs(self, event=None):
        """Фильтрует список PDF в Combobox."""
        search_term = self.pdf_selector.get().lower()
        if not search_term:
            self.pdf_selector["values"] = self.all_pdf_files
            return
        filtered = [f for f in self.all_pdf_files if search_term in f.lower()]
        self.pdf_selector["values"] = filtered

    def add_to_list(self):
        """Добавляет выбранный PDF в список на печать."""
        filename = self.pdf_selector.get()
        if not filename or filename not in self.all_pdf_files:
            messagebox.showwarning("Внимание", "Выберите корректный PDF-файл.")
            return

        try:
            quantity = int(self.quantity_input.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror("Ошибка", "Количество должно быть целым числом > 0.")
            return

        self.selected_for_printing[filename] = quantity
        self.update_print_list_view()
        self.show_pdf_preview(filename)
        self.app.update_status(f"Добавлен: {filename} (x{quantity})")

    def update_print_list_view(self):
        """Обновляет Treeview со списком PDF."""
        for i in self.print_list_view.get_children():
            self.print_list_view.delete(i)
        for filename, quantity in self.selected_for_printing.items():
            self.print_list_view.insert("", tk.END, values=(filename, quantity, "❌"))

    def clear_list(self, silent=False):
        """Очищает список для печати."""
        if not self.selected_for_printing and not silent:
            return
        self.selected_for_printing.clear()
        self.update_print_list_view()
        if not silent:
            self.show_pdf_preview(None)
            self.app.update_status("Список для печати с ленты очищен.")

    def handle_list_click(self, event):
        """Обрабатывает клик по списку для удаления строки."""
        column_id = self.print_list_view.identify_column(event.x)
        if column_id == "#3":  # Столбец "Удалить"
            item_id = self.print_list_view.identify_row(event.y)
            if item_id:
                filename = self.print_list_view.item(item_id, "values")[0]
                if filename in self.selected_for_printing:
                    del self.selected_for_printing[filename]
                    self.update_print_list_view()
                    self.app.update_status(f"Удалено: {filename}")

    def edit_list_item(self, event):
        """Обрабатывает двойной клик для редактирования количества."""
        item_id = self.print_list_view.identify_row(event.y)
        column_id = self.print_list_view.identify_column(event.x)

        # Редактируем только столбец "Количество" (индекс #2)
        if not item_id or column_id != "#2":
            return

        x, y, width, height = self.print_list_view.bbox(item_id, column_id)
        current_value = self.print_list_view.item(item_id, "values")[1]

        entry = ttk.Entry(self.print_list_view)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.focus_set()

        entry.bind("<FocusOut>", lambda e: self.save_edited_quantity(e, entry, item_id))
        entry.bind("<Return>", lambda e: self.save_edited_quantity(e, entry, item_id))

    def save_edited_quantity(self, event, entry_widget, item_id):
        """Сохраняет новое значение количества и уничтожает поле ввода."""
        new_value_str = entry_widget.get()
        try:
            new_quantity = int(new_value_str)
            if new_quantity <= 0:
                raise ValueError("Количество должно быть положительным")

            filename = self.print_list_view.item(item_id, "values")[0]
            if filename in self.selected_for_printing:
                self.selected_for_printing[filename] = new_quantity
                self.app.update_status(f"Количество для '{filename}' обновлено.")

            self.update_print_list_view()

        except ValueError:
            messagebox.showerror(
                "Ошибка ввода", "Количество должно быть целым положительным числом."
            )
        finally:
            entry_widget.destroy()

    def show_pdf_preview(self, filename):
        """Отображает первую страницу PDF в области предпросмотра."""
        if not filename:
            self.preview_label.config(image="", text="Выберите PDF-файл")
            self.preview_image = None
            return

        filepath = os.path.join(self.app.pdf_source_dir, filename)
        if not os.path.exists(filepath):
            self.preview_label.config(image="", text="Файл не найден")
            self.preview_image = None
            return

        try:
            doc = fitz.open(filepath)
            if len(doc) == 0:
                self.preview_label.config(image="", text="PDF пустой")
                self.preview_image = None
                doc.close()
                return

            page = doc.load_page(0)

            # Рассчитываем масштабирование, чтобы ширина была около 300 пикселей
            target_width = 300
            page_width = page.rect.width
            zoom = target_width / page_width if page_width > 0 else 1
            mat = fitz.Matrix(zoom, zoom)  # Создаем матрицу масштабирования
            pix = page.get_pixmap(matrix=mat)

            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # Создаем PhotoImage и сохраняем на него ссылку
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_image, text="")
            doc.close()

        except Exception as e:
            print(f"Ошибка загрузки превью PDF: {e}")
            self.preview_label.config(image="", text="Ошибка\nзагрузки PDF")
            self.preview_image = None

    def update_preview_from_combobox(self, event=None):
        """Обновляет превью на основе выбора в Combobox."""
        selected_file = self.pdf_selector.get()
        self.show_pdf_preview(selected_file)

    def update_preview_from_list(self, event=None):
        """Обновляет превью на основе выбора в Treeview."""
        selected_items = self.print_list_view.selection()
        if not selected_items:
            return

        item_id = selected_items[0]
        filename = self.print_list_view.item(item_id, "values")[0]
        self.show_pdf_preview(filename)

    def process_ribbon_printing(self):
        """Запускает процесс объединения PDF и отправки на печать."""
        if not self.selected_for_printing:
            messagebox.showwarning("Внимание", "Список для печати пуст.")
            return

        if not self.app.selected_printer:
            messagebox.showerror("Ошибка", "Принтер не выбран в Настройках.")
            return

        temp_fd, temp_path = tempfile.mkstemp(suffix=".pdf")
        os.close(temp_fd)

        try:
            self.app.update_status("Объединение PDF-файлов...")
            pdf_generator.merge_pdfs(
                self.selected_for_printing, self.app.pdf_source_dir, temp_path
            )

            self.app.update_status(
                f"Отправка на принтер {self.app.selected_printer}..."
            )
            win32api.ShellExecute(
                0, "printto", temp_path, f'"{self.app.selected_printer}"', ".", 0
            )
            self.app.update_status("Документ отправлен на печать.")
            messagebox.showinfo("Готово", "Задание на печать успешно отправлено.")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{e}")
            self.app.update_status("Ошибка при печати с ленты.")
        finally:
            if os.path.exists(temp_path):
                # Даем небольшую задержку перед удалением, чтобы принтер успел "схватить" файл
                self.app.after(2000, lambda: os.remove(temp_path))
