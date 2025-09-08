import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import pdf_generator


class BarcodePDFApp(tk.Tk):
    """
    Основной класс приложения для генерации PDF со штрих-кодами.
    """

    def __init__(self):
        super().__init__()

        # --- Базовая настройка окна ---
        self.title("Генератор PDF со штрих-кодами")
        self.geometry("550x600")  # Немного шире для нового интерфейса

        # --- Конфигурация ---
        # Заменяем локальный путь на ваш сетевой путь
        self.barcode_dir = r"barcode_images"
        # Словарь для хранения выбранных для генерации файлов {имя_файла: количество}
        self.selected_for_generation = {}

        # --- Создание виджетов ---
        self.create_widgets()

        # --- Загрузка списка штрих-кодов при запуске ---
        self.load_barcode_list()

    def create_widgets(self):
        """
        Создает все основные элементы интерфейса.
        """
        # --- 1. Фрейм для выбора штрих-кода ---
        selection_frame = ttk.LabelFrame(
            self, text="Шаг 1: Выбор штрих-кода", padding=(10, 5)
        )
        selection_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(selection_frame, text="Штрих-код:").grid(
            row=0, column=0, padx=(0, 5), sticky="w"
        )
        self.barcode_selector = ttk.Combobox(
            selection_frame, state="readonly", width=30
        )
        self.barcode_selector.grid(row=0, column=1, padx=5, sticky="ew")

        ttk.Label(selection_frame, text="Кол-во:").grid(
            row=0, column=2, padx=(10, 5), sticky="w"
        )
        self.quantity_input = ttk.Entry(selection_frame, width=8)
        self.quantity_input.insert(0, "1")
        self.quantity_input.grid(row=0, column=3, padx=5, sticky="w")

        add_button = ttk.Button(
            selection_frame, text="Добавить", command=self.add_to_list
        )
        add_button.grid(row=0, column=4, padx=(10, 0))

        selection_frame.columnconfigure(1, weight=1)

        # --- 2. Фрейм для списка на генерацию ---
        list_frame = ttk.LabelFrame(
            self, text="Шаг 2: Список для генерации PDF", padding=(10, 5)
        )
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        columns = ("filename", "quantity")
        self.generation_list_view = ttk.Treeview(
            list_frame, columns=columns, show="headings"
        )
        self.generation_list_view.heading("filename", text="Имя файла")
        self.generation_list_view.heading("quantity", text="Количество")
        self.generation_list_view.column("quantity", width=100, anchor="center")

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.generation_list_view.yview
        )
        self.generation_list_view.configure(yscrollcommand=scrollbar.set)

        self.generation_list_view.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        remove_button = ttk.Button(
            self, text="Удалить выбранное", command=self.remove_from_list
        )
        remove_button.pack(pady=5)

        # --- 3. Кнопка "Сгенерировать PDF" ---
        generate_button = ttk.Button(
            self, text="Сгенерировать PDF", command=self.process_generation
        )
        generate_button.pack(pady=(5, 10))

    def load_barcode_list(self):
        """
        Сканирует папку barcode_images и заполняет выпадающий список.
        """
        if not os.path.isdir(self.barcode_dir):
            messagebox.showerror(
                "Ошибка",
                f"Папка '{self.barcode_dir}' не найдена.\nПожалуйста, создайте ее и поместите туда изображения штрих-кодов.",
            )
            self.destroy()
            return

        # Получаем список файлов-изображений
        barcode_files = sorted(
            [
                f
                for f in os.listdir(self.barcode_dir)
                if f.lower().endswith((".png", ".jpg", ".jpeg"))
            ]
        )

        if not barcode_files:
            messagebox.showwarning(
                "Внимание", f"В папке '{self.barcode_dir}' не найдено изображений."
            )
            self.barcode_selector["values"] = []
        else:
            self.barcode_selector["values"] = barcode_files
            self.barcode_selector.current(0)  # Выбрать первый элемент по умолчанию

    def add_to_list(self):
        """Добавляет выбранный штрих-код и количество в итоговый список."""
        filename = self.barcode_selector.get()
        if not filename:
            messagebox.showwarning(
                "Внимание", "Пожалуйста, выберите штрих-код из списка."
            )
            return

        try:
            quantity = int(self.quantity_input.get())
            if quantity <= 0:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Ошибка", "Количество должно быть целым положительным числом."
            )
            return

        # Добавляем или обновляем значение в словаре
        self.selected_for_generation[filename] = quantity

        # Обновляем Treeview
        self.update_generation_list_view()

        # Сбрасываем поля для удобства
        self.quantity_input.delete(0, tk.END)
        self.quantity_input.insert(0, "1")
        self.barcode_selector.set("")  # Очищаем выбор

    def remove_from_list(self):
        """Удаляет выбранные элементы из итогового списка."""
        selected_items = self.generation_list_view.selection()
        if not selected_items:
            messagebox.showwarning(
                "Внимание", "Выберите элементы для удаления из списка."
            )
            return

        for item_id in selected_items:
            # Получаем имя файла из Treeview
            filename = self.generation_list_view.item(item_id, "values")[0]
            # Удаляем из словаря
            if filename in self.selected_for_generation:
                del self.selected_for_generation[filename]

        # Обновляем Treeview
        self.update_generation_list_view()

    def update_generation_list_view(self):
        """Обновляет виджет Treeview на основе данных из словаря."""
        # Очищаем старые записи
        for i in self.generation_list_view.get_children():
            self.generation_list_view.delete(i)

        # Добавляем новые из словаря
        for filename, quantity in sorted(self.selected_for_generation.items()):
            self.generation_list_view.insert("", tk.END, values=(filename, quantity))

    def process_generation(self):
        """
        Обрабатывает нажатие на кнопку "Сгенерировать PDF".
        """
        # Теперь данные берутся из self.selected_for_generation
        selected_barcodes = self.selected_for_generation

        if not selected_barcodes:
            messagebox.showwarning(
                "Внимание",
                "Список для генерации пуст. Добавьте хотя бы один штрих-код.",
            )
            return

        print("Выбранные штрих-коды для генерации:", selected_barcodes)

        # --- Диалог сохранения файла ---
        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")],
            title="Сохранить PDF файл как...",
        )

        if not file_path:
            # Пользователь нажал "Отмена" в диалоге сохранения
            print("Генерация отменена пользователем.")
            return

        # --- Вызов реальной логики генерации PDF ---
        try:
            # Временно блокируем окно, чтобы пользователь не мог ничего нажать во время генерации
            self.attributes("-disabled", True)
            self.update_idletasks()  # Обновляем интерфейс

            pdf_generator.create_pdf_from_barcodes(
                selected_barcodes, self.barcode_dir, file_path
            )

            messagebox.showinfo(
                "Готово",
                f"PDF-файл успешно создан и сохранен как:\n{os.path.basename(file_path)}",
            )
        except Exception as e:
            # Отлавливаем любые ошибки из модуля генерации и сообщаем пользователю
            print(f"Ошибка при создании PDF: {e}")
            messagebox.showerror("Ошибка генерации", f"Произошла ошибка:\n{e}")
        finally:
            # Разблокируем окно в любом случае (даже после ошибки)
            self.attributes("-disabled", False)


if __name__ == "__main__":
    app = BarcodePDFApp()
    app.mainloop()
