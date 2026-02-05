import configparser
import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import win32api
import win32print
from PIL import Image, ImageTk

import pdf_generator


class BarcodePDFApp(tk.Tk):
    """
    Основной класс приложения для генерации PDF со штрих-кодами.
    """

    def __init__(self):
        super().__init__()

        # --- Базовая настройка окна ---
        self.title("Генератор PDF со штрих-кодами")
        self.geometry("850x600")  # Шире для предпросмотра

        # --- Конфигурация ---
        self.config_file = "config.ini"
        self.barcode_dir = r"barcode_images"  # Значение по умолчанию
        self.load_config()  # Загружаем путь из файла

        # Словарь для хранения выбранных для генерации файлов {имя_файла: количество}
        self.selected_for_generation = {}
        # Список для хранения всех найденных файлов для поиска
        self.all_barcode_files = []
        # Ссылка на изображение для предпросмотра, чтобы его не удалил сборщик мусора
        self.preview_image = None

        # --- Создание виджетов ---
        self.create_widgets()

        # --- Загрузка списка штрих-кодов при запуске ---
        self.load_barcode_list()

    def load_config(self):
        """Загружает конфигурацию из файла .ini."""
        config = configparser.ConfigParser()
        if os.path.exists(self.config_file):
            config.read(self.config_file, encoding="utf-8")
            self.barcode_dir = config.get(
                "Settings", "BarcodeDir", fallback=self.barcode_dir
            )

    def save_config(self):
        """Сохраняет текущую конфигурацию в файл .ini."""
        config = configparser.ConfigParser()
        config["Settings"] = {"BarcodeDir": self.barcode_dir}
        with open(self.config_file, "w", encoding="utf-8") as configfile:
            config.write(configfile)

    def create_widgets(self):
        """
        Создает все основные элементы интерфейса.
        """
        # --- Создание верхнего меню ---
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # Меню "Файл"
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)

        # Меню "Справка"
        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about_dialog)
        menubar.add_cascade(label="Справка", menu=help_menu)

        # --- Создание вкладок ---
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        main_tab = ttk.Frame(notebook)
        settings_tab = ttk.Frame(notebook)

        notebook.add(main_tab, text="Главная")
        notebook.add(settings_tab, text="Настройки")

        # --- Заполнение основной вкладки ---
        self.create_main_tab(main_tab)

        # --- Заполнение вкладки настроек ---
        self.create_settings_tab(settings_tab)

        # --- 5. Статус-бар ---
        self.status_bar = ttk.Label(
            self, text="Загрузка...", anchor="w", relief=tk.SUNKEN
        )
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

    def create_main_tab(self, parent_tab):
        """Создает виджеты для основной вкладки."""
        main_frame = ttk.Frame(parent_tab)
        main_frame.pack(fill="both", expand=True)

        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="y", expand=False)

        # --- 1. Фрейм для выбора штрих-кода ---
        selection_frame = ttk.LabelFrame(
            left_panel, text="Шаг 1: Выбор штрих-кода", padding=(10, 5)
        )
        selection_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(selection_frame, text="Штрих-код:").grid(
            row=0, column=0, padx=(0, 5), sticky="w"
        )
        self.barcode_selector = ttk.Combobox(selection_frame, state="normal", width=30)
        self.barcode_selector.grid(row=0, column=1, padx=5, sticky="ew")
        # Обновляем предпросмотр при выборе из списка
        self.barcode_selector.bind(
            "<<ComboboxSelected>>", self.update_preview_from_combobox
        )
        self.barcode_selector.bind("<KeyRelease>", self.filter_barcodes)

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
            left_panel, text="Шаг 2: Список для генерации PDF", padding=(10, 5)
        )
        list_frame.pack(fill="both", expand=True, pady=5)

        columns = ("filename", "quantity", "delete")
        self.generation_list_view = ttk.Treeview(
            list_frame, columns=columns, show="headings"
        )
        self.generation_list_view.heading("filename", text="Имя файла")
        self.generation_list_view.heading("quantity", text="Количество")
        self.generation_list_view.heading("delete", text="Удалить")
        self.generation_list_view.column("quantity", width=100, anchor="center")
        self.generation_list_view.column("delete", width=60, anchor="center")

        # Добавляем скроллбар
        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.generation_list_view.yview
        )
        self.generation_list_view.configure(yscrollcommand=scrollbar.set)

        self.generation_list_view.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Фрейм для итогового счетчика
        total_frame = ttk.Frame(list_frame)
        total_frame.pack(fill="x", side="bottom", pady=(5, 0))
        self.total_count_label = ttk.Label(total_frame, text="Всего для печати: 0")
        self.total_count_label.pack(side="right")

        # Привязываем событие клика к новому методу
        self.generation_list_view.bind("<ButtonPress-1>", self.on_drag_start)
        self.generation_list_view.bind("<B1-Motion>", self.on_drag_motion)
        self.generation_list_view.bind("<ButtonRelease-1>", self.on_drag_release)

        # Обновляем предпросмотр при выборе из списка
        self.generation_list_view.bind(
            "<<TreeviewSelect>>", self.update_preview_from_list
        )
        # Привязываем событие двойного клика для редактирования
        self.generation_list_view.bind("<Double-1>", self.edit_list_item)

        # --- 3. Кнопки управления списком и генерации ---
        clear_button = ttk.Button(
            left_panel, text="Убрать все", command=self.clear_list
        )
        clear_button.pack(pady=5)

        # --- 3. Кнопка "Сгенерировать PDF" ---
        generate_button = ttk.Button(
            left_panel, text="Сгенерировать PDF", command=self.process_generation
        )
        generate_button.pack(pady=(5, 0))

        # --- Новая кнопка "Сгенерировать и печатать" ---
        print_button = ttk.Button(
            left_panel, text="Сгенерировать и печатать", command=self.process_printing
        )
        print_button.pack(pady=(5, 10))

        # --- 4. Фрейм для предпросмотра ---
        preview_frame = ttk.LabelFrame(right_panel, text="Предпросмотр", padding=10)
        preview_frame.pack(fill="both", expand=True)

        self.preview_label = ttk.Label(preview_frame, text="Выберите штрих-код")
        self.preview_label.pack(fill="both", expand=True)

    def create_settings_tab(self, parent_tab):
        """Создает виджеты для вкладки настроек."""
        settings_frame = ttk.LabelFrame(
            parent_tab, text="Путь к изображениям", padding=15
        )
        settings_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(settings_frame, text="Папка со штрих-кодами:").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        self.path_entry = ttk.Entry(settings_frame, width=70)
        self.path_entry.insert(0, self.barcode_dir)
        self.path_entry.config(state="readonly")
        self.path_entry.grid(row=1, column=0, sticky="ew")

        browse_button = ttk.Button(
            settings_frame, text="Выбрать...", command=self.select_barcode_dir
        )
        browse_button.grid(row=1, column=1, sticky="w", padx=(10, 0))

        settings_frame.columnconfigure(0, weight=1)

    def load_barcode_list(self):
        """
        Сканирует папку barcode_images и заполняет выпадающий список.
        """
        # Очищаем старые данные перед загрузкой новых
        self.clear_list(silent=True)
        self.barcode_selector.set("")

        if not os.path.isdir(self.barcode_dir):
            messagebox.showwarning(
                "Папка не найдена",
                f"Папка '{self.barcode_dir}' не найдена.\n\n"
                "Пожалуйста, укажите правильный путь на вкладке 'Настройки'.",
            )
            self.barcode_selector["values"] = []
            self.all_barcode_files = []
            self.update_status("Ошибка: неверный путь к папке со штрих-кодами.")
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
            self.all_barcode_files = []
            self.update_status("Внимание: Изображения не найдены.")
        else:
            self.all_barcode_files = barcode_files
            self.barcode_selector["values"] = self.all_barcode_files
            self.barcode_selector.current(0)  # Выбрать первый элемент по умолчанию
            self.show_preview(
                self.barcode_selector.get()
            )  # Показать превью первого элемента
            self.update_status("Готово")

    def show_preview(self, filename):
        """Отображает изображение штрих-кода в области предпросмотра."""
        if not filename:
            # Очищаем предпросмотр, если имя файла не передано
            self.preview_label.config(image="", text="Выберите штрих-код")
            self.preview_image = None
            return

        filepath = os.path.join(self.barcode_dir, filename)
        if not os.path.exists(filepath):
            self.preview_label.config(image="", text="Файл не найден")
            self.preview_image = None
            return

        try:
            # Открываем изображение и масштабируем его для предпросмотра
            img = Image.open(filepath)

            # Задаем максимальную ширину для предпросмотра
            max_width = 250
            w_percent = max_width / float(img.size[0])
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)

            # Создаем PhotoImage и сохраняем на него ссылку
            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_image, text="")
        except Exception as e:
            print(f"Ошибка загрузки превью: {e}")
            self.preview_label.config(image="", text="Ошибка\nзагрузки")
            self.preview_image = None

    def update_preview_from_combobox(self, event=None):
        """Обновляет превью на основе выбора в Combobox."""
        selected_file = self.barcode_selector.get()
        self.show_preview(selected_file)

    def select_barcode_dir(self):
        """Открывает диалог выбора папки и обновляет путь."""
        new_dir = filedialog.askdirectory(
            title="Выберите папку со штрих-кодами", initialdir=self.barcode_dir
        )

        if new_dir and new_dir != self.barcode_dir:
            self.barcode_dir = new_dir
            self.update_status(f"Новый путь: {self.barcode_dir}")

            # Обновляем поле ввода в настройках
            self.path_entry.config(state="normal")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.barcode_dir)
            self.path_entry.config(state="readonly")

            # Сохраняем и перезагружаем список
            self.save_config()
            self.load_barcode_list()

    def filter_barcodes(self, event=None):
        """Фильтрует список в Combobox на основе введенного текста."""
        search_term = self.barcode_selector.get().lower()

        if not search_term:
            # Если поле поиска пустое, показываем все штрих-коды
            self.barcode_selector["values"] = self.all_barcode_files
            return

        # Фильтруем список
        filtered_files = [f for f in self.all_barcode_files if search_term in f.lower()]
        self.barcode_selector["values"] = filtered_files

    def add_to_list(self):
        """Добавляет выбранный штрих-код и количество в список для генерации."""
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

        # Проверяем, что выбранный файл действительно существует в исходном списке
        if filename not in self.all_barcode_files:
            messagebox.showwarning(
                "Внимание",
                f"Файл '{filename}' не найден в списке. Выберите корректный файл.",
            )
            return

        # Добавляем или обновляем значение в словаре
        self.selected_for_generation[filename] = quantity

        # Обновляем Treeview
        self.update_generation_list_view()
        self.update_status(f"Добавлен: {filename}")

        # Сбрасываем поля для удобства
        self.quantity_input.delete(0, tk.END)
        self.quantity_input.insert(0, "1")
        self.barcode_selector.set("")  # Очищаем выбор

    def update_preview_from_list(self, event=None):
        """Обновляет превью на основе выбора в Treeview."""
        selected_items = self.generation_list_view.selection()
        if not selected_items:
            return

        item_id = selected_items[0]  # Берем первый выделенный элемент
        filename = self.generation_list_view.item(item_id, "values")[0]
        self.show_preview(filename)

    def handle_list_click(self, event):
        """Обрабатывает клик по списку для удаления отдельной строки."""
        column_id = self.generation_list_view.identify_column(event.x)
        # Проверяем, что клик был по третьему столбцу (индекс #3)
        if column_id == "#3":
            item_id = self.generation_list_view.identify_row(event.y)
            if item_id:
                # Получаем имя файла из строки
                filename = self.generation_list_view.item(item_id, "values")[0]
                if filename in self.selected_for_generation:
                    del self.selected_for_generation[filename]
                    self.update_generation_list_view()

    def edit_list_item(self, event):
        """Обрабатывает двойной клик для редактирования количества."""
        item_id = self.generation_list_view.identify_row(event.y)
        column_id = self.generation_list_view.identify_column(event.x)

        # Редактируем только столбец "Количество" (индекс #2)
        if not item_id or column_id != "#2":
            return

        # Получаем координаты ячейки
        x, y, width, height = self.generation_list_view.bbox(item_id, column_id)

        # Создаем временное поле для ввода
        current_value = self.generation_list_view.item(item_id, "values")[1]
        entry = ttk.Entry(self.generation_list_view)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.focus_set()

        # Привязываем события для сохранения значения
        entry.bind(
            "<FocusOut>",
            lambda e: self.save_edited_quantity(e, entry, item_id),
        )
        entry.bind(
            "<Return>",
            lambda e: self.save_edited_quantity(e, entry, item_id),
        )

    def save_edited_quantity(self, event, entry_widget, item_id):
        """Сохраняет новое значение количества и уничтожает поле ввода."""
        new_value_str = entry_widget.get()

        try:
            new_quantity = int(new_value_str)
            if new_quantity <= 0:
                raise ValueError("Количество должно быть положительным")

            # Получаем имя файла из строки
            filename = self.generation_list_view.item(item_id, "values")[0]

            # Обновляем значение в нашем основном словаре
            if filename in self.selected_for_generation:
                self.selected_for_generation[filename] = new_quantity
                self.update_status(f"Количество для '{filename}' обновлено")

            # Обновляем весь список
            self.update_generation_list_view()

        except ValueError:
            messagebox.showerror(
                "Ошибка ввода", "Количество должно быть целым положительным числом."
            )
            # Не обновляем список, чтобы пользователь видел ошибку

        finally:
            # Уничтожаем временное поле ввода в любом случае
            entry_widget.destroy()

    def clear_list(self, silent=False):
        """Полностью очищает список для генерации."""
        if not self.selected_for_generation:
            return  # Ничего не делаем, если список уже пуст

        self.selected_for_generation.clear()
        self.update_generation_list_view()
        if not silent:
            self.update_status("Список очищен. Готово")
        self.show_preview(None)  # Очищаем предпросмотр

    def on_drag_start(self, event):
        """Запоминает выбранный для перетаскивания элемент."""
        # Сначала проверяем, не был ли это клик для удаления
        column_id = self.generation_list_view.identify_column(event.x)
        if column_id == "#3":
            self.handle_list_click(event)
            return "break"  # Прерываем дальнейшую обработку, чтобы не начать drag

        # Если это не удаление, начинаем перетаскивание
        if self.generation_list_view.identify_row(event.y):
            self.generation_list_view.selection_set(
                self.generation_list_view.identify_row(event.y)
            )

    def on_drag_motion(self, event):
        """Перемещает элемент в списке во время движения мыши."""
        if not self.generation_list_view.selection():
            return

        moveto_item = self.generation_list_view.identify_row(event.y)
        if moveto_item:
            self.generation_list_view.move(
                self.generation_list_view.selection()[0],
                "",
                self.generation_list_view.index(moveto_item),
            )

    def on_drag_release(self, event):
        """Обновляет порядок в словаре данных после перетаскивания."""
        new_order = self.generation_list_view.get_children()
        new_selected = {
            self.generation_list_view.item(item, "values")[
                0
            ]: self.selected_for_generation[
                self.generation_list_view.item(item, "values")[0]
            ]
            for item in new_order
        }
        self.selected_for_generation = new_selected
        self.update_status("Порядок элементов изменен")

    def update_status(self, message):
        """Обновляет текст в статус-баре."""
        self.status_bar.config(text=message)
        self.update_idletasks()

    def show_about_dialog(self):
        """Показывает диалоговое окно "О программе"."""
        messagebox.showinfo(
            "О программе",
            "Генератор PDF со штрих-кодами\n\n"
            "Версия: 1.1\n\n"
            "Приложение для удобного создания PDF-документов из изображений штрих-кодов.",
        )

    def update_total_count(self):
        """Подсчитывает и обновляет общее количество штрих-кодов для печати."""
        total_quantity = sum(self.selected_for_generation.values())
        self.total_count_label.config(text=f"Всего для печати: {total_quantity}")

    def update_generation_list_view(self):
        """Обновляет виджет Treeview на основе данных из словаря."""
        # Очищаем старые записи
        for i in self.generation_list_view.get_children():
            self.generation_list_view.delete(i)

        # Добавляем новые из словаря
        for filename, quantity in self.selected_for_generation.items():
            self.generation_list_view.insert(
                "", tk.END, values=(filename, quantity, "❌")
            )

        # Обновляем общий счетчик
        self.update_total_count()

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
            self.update_status("Генерация отменена. Готово")
            return

        # --- Вызов реальной логики генерации PDF ---
        try:
            # Временно блокируем окно, чтобы пользователь не мог ничего нажать во время генерации
            self.attributes("-disabled", True)
            self.update_status("Генерация PDF...")
            self.update_idletasks()  # Обновляем интерфейс

            pdf_generator.create_pdf_from_barcodes(
                selected_barcodes,
                self.barcode_dir,
                file_path,
                title=os.path.splitext(os.path.basename(file_path))[0],
            )

            messagebox.showinfo(
                "Готово",
                f"PDF-файл успешно создан и сохранен как:\n{os.path.basename(file_path)}",
            )
            self.update_status(
                f"PDF-файл успешно создан: {os.path.basename(file_path)}"
            )
        except Exception as e:
            # Отлавливаем любые ошибки из модуля генерации и сообщаем пользователю
            print(f"Ошибка при создании PDF: {e}")
            messagebox.showerror("Ошибка генерации", f"Произошла ошибка:\n{e}")
            self.update_status("Ошибка при генерации PDF. Готово")
        finally:
            # Разблокируем окно в любом случае (даже после ошибки)
            self.attributes("-disabled", False)
            self.focus_set()  # Возвращаем фокус окну

    def process_printing(self):
        """
        Обрабатывает нажатие на кнопку "Сгенерировать и печатать".
        """
        selected_barcodes = self.selected_for_generation
        if not selected_barcodes:
            messagebox.showwarning("Внимание", "Список для генерации пуст.")
            return

        temp_file_descriptor, temp_file_path = tempfile.mkstemp(suffix=".pdf")
        os.close(temp_file_descriptor)

        try:
            self.attributes("-disabled", True)
            self.update_status("Генерация PDF для печати...")
            self.update_idletasks()

            pdf_generator.create_pdf_from_barcodes(
                selected_barcodes,
                self.barcode_dir,
                temp_file_path,
                title="Печать штрих-кодов",
            )

            self.update_status("Отправка на печать...")
            self.update_idletasks()

            # Проверяем, есть ли принтер по умолчанию
            try:
                win32print.GetDefaultPrinter()
            except RuntimeError:
                messagebox.showerror("Ошибка печати", "Принтер по умолчанию не найден.")
                return

            win32api.ShellExecute(0, "print", temp_file_path, "", ".", 0)
            self.update_status("Документ отправлен на печать. Готово.")
            messagebox.showinfo("Печать", "Документ отправлен на печать.")

        except Exception as e:
            print(f"Ошибка при генерации или печати PDF: {e}")
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{e}")
            self.update_status("Ошибка при печати. Готово.")
        finally:
            self.attributes("-disabled", False)
            self.focus_set()


if __name__ == "__main__":
    app = BarcodePDFApp()
    app.mainloop()
