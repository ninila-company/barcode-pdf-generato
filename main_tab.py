from __future__ import annotations

import os
import tempfile
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, Optional

import win32api
from PIL import Image, ImageTk

import pdf_generator
import preview_window


class MainTab(ttk.Frame):

    def __init__(self, parent: ttk.Notebook, app):
        super().__init__(parent)
        self.app = app

        self.selected_for_generation: Dict[str, int] = {}
        self.all_barcode_files: list[str] = []
        self.preview_image: Optional[ImageTk.PhotoImage] = None

        self.create_widgets()

    def create_widgets(self):
        main_frame = ttk.Frame(self)
        main_frame.pack(fill="both", expand=True)

        left_panel = ttk.Frame(main_frame)
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_panel = ttk.Frame(main_frame)
        right_panel.pack(side="right", fill="y", expand=False)

        selection_frame = ttk.LabelFrame(
            left_panel, text="Шаг 1: Выбор штрих-кода", padding=(10, 5)
        )
        selection_frame.pack(fill="x", pady=(0, 5))

        ttk.Label(selection_frame, text="Штрих-код:").grid(
            row=0, column=0, padx=(0, 5), sticky="w"
        )
        self.barcode_selector = ttk.Combobox(
            selection_frame, state="normal", width=30, height=20
        )
        self.barcode_selector.grid(row=0, column=1, padx=5, sticky="ew")
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
            selection_frame,
            text="Добавить",
            command=self.add_to_list,
            style="Success.TButton",
        )
        add_button.grid(row=0, column=4, padx=(10, 0))

        selection_frame.columnconfigure(1, weight=1)

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

        scrollbar = ttk.Scrollbar(
            list_frame, orient="vertical", command=self.generation_list_view.yview
        )
        self.generation_list_view.configure(yscrollcommand=scrollbar.set)

        self.generation_list_view.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        total_frame = ttk.Frame(list_frame)
        total_frame.pack(fill="x", side="bottom", pady=(5, 0))
        self.total_count_label = ttk.Label(total_frame, text="Всего для печати: 0")
        self.total_count_label.pack(side="right")

        self.generation_list_view.bind("<ButtonPress-1>", self.on_drag_start)
        self.generation_list_view.bind("<B1-Motion>", self.on_drag_motion)
        self.generation_list_view.bind("<ButtonRelease-1>", self.on_drag_release)

        self.generation_list_view.bind(
            "<<TreeviewSelect>>", self.update_preview_from_list
        )
        self.generation_list_view.bind("<Double-1>", self.edit_list_item)

        clear_button = ttk.Button(
            left_panel,
            text="Убрать все",
            command=self.clear_list,
            style="Danger.TButton",
        )
        clear_button.pack(pady=5)

        generate_button = ttk.Button(
            left_panel,
            text="Сгенерировать PDF",
            command=self.process_generation,
            style="Success.TButton",
        )
        generate_button.pack(pady=(5, 0))

        print_button = ttk.Button(
            left_panel,
            text="Сгенерировать и печатать",
            command=self.process_printing,
            style="Success.TButton",
        )
        print_button.pack(pady=(5, 10))

        preview_button = ttk.Button(
            left_panel,
            text="Предпросмотр PDF",
            command=self.process_preview,
            style="TButton",
        )
        preview_button.pack(pady=(0, 10))

        preview_frame = ttk.LabelFrame(right_panel, text="Предпросмотр", padding=10)
        preview_frame.pack(fill="both", expand=True)

        self.preview_label = ttk.Label(
            preview_frame,
            text="Выберите штрих-код",
            background=self.app.FRAME_BG,
        )
        self.preview_label.pack(fill="both", expand=True)

    def set_barcodes(self, files: list[str]) -> None:
        self.all_barcode_files = files
        self.barcode_selector["values"] = files
        if files:
            self.barcode_selector.current(0)
            self.show_preview(self.barcode_selector.get())

    def show_preview(self, filename: Optional[str]) -> None:
        if not filename:
            self.preview_label.config(image="", text="Выберите штрих-код")
            self.preview_image = None
            return

        filepath = os.path.join(self.app.cfg.barcode_dir, filename)
        if not os.path.exists(filepath):
            self.preview_label.config(image="", text="Файл не найден")
            self.preview_image = None
            return

        try:
            img = Image.open(filepath)
            max_width = 250
            w_percent = max_width / float(img.size[0])
            h_size = int((float(img.size[1]) * float(w_percent)))
            img = img.resize((max_width, h_size), Image.Resampling.LANCZOS)

            self.preview_image = ImageTk.PhotoImage(img)
            self.preview_label.config(image=self.preview_image, text="")
        except Exception as e:
            print(f"Ошибка загрузки превью: {e}")
            self.preview_label.config(image="", text="Ошибка\nзагрузки")
            self.preview_image = None

    def update_preview_from_combobox(self, event=None):
        selected_file = self.barcode_selector.get()
        self.show_preview(selected_file)

    def update_preview_from_list(self, event=None):
        selected_items = self.generation_list_view.selection()
        if not selected_items:
            return
        item_id = selected_items[0]
        filename = self.generation_list_view.item(item_id, "values")[0]
        self.show_preview(filename)

    def filter_barcodes(self, event=None):
        search_term = self.barcode_selector.get().lower()
        if not search_term:
            self.barcode_selector["values"] = self.all_barcode_files
            return
        filtered = [f for f in self.all_barcode_files if search_term in f.lower()]
        self.barcode_selector["values"] = filtered

    def add_to_list(self):
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

        if filename not in self.all_barcode_files:
            messagebox.showwarning(
                "Внимание",
                f"Файл '{filename}' не найден в списке. Выберите корректный файл.",
            )
            return

        self.selected_for_generation[filename] = quantity
        self.update_generation_list_view()
        self.app.update_status(f"Добавлен: {filename}")

        self.quantity_input.delete(0, tk.END)
        self.quantity_input.insert(0, "1")
        self.barcode_selector.set("")
        self.barcode_selector.focus_set()

    def add_barcodes_from_selection(self, checkbox_vars: dict) -> int:
        added_count = 0
        for filename, var in checkbox_vars.items():
            if var.get() == 1:
                if filename not in self.selected_for_generation:
                    self.selected_for_generation[filename] = 1
                    added_count += 1
                var.set(0)
        if added_count > 0:
            self.update_generation_list_view()
        return added_count

    def switch_to_main_tab(self):
        self.app.notebook.select(self)

    def update_total_count(self):
        total = sum(self.selected_for_generation.values())
        self.total_count_label.config(text=f"Всего для печати: {total}")

    def update_generation_list_view(self):
        for i in self.generation_list_view.get_children():
            self.generation_list_view.delete(i)

        for filename, quantity in self.selected_for_generation.items():
            self.generation_list_view.insert(
                "", tk.END, values=(filename, quantity, "❌")
            )

        self.update_total_count()

    def clear_list(self, silent: bool = False):
        if not self.selected_for_generation:
            return
        self.selected_for_generation.clear()
        self.update_generation_list_view()
        if not silent:
            self.app.update_status("Список очищен. Готово")
        self.show_preview(None)

    def handle_list_click(self, event):
        column_id = self.generation_list_view.identify_column(event.x)
        if column_id == "#3":
            item_id = self.generation_list_view.identify_row(event.y)
            if item_id:
                filename = self.generation_list_view.item(item_id, "values")[0]
                if filename in self.selected_for_generation:
                    del self.selected_for_generation[filename]
                    self.update_generation_list_view()

    def edit_list_item(self, event):
        item_id = self.generation_list_view.identify_row(event.y)
        column_id = self.generation_list_view.identify_column(event.x)

        if not item_id or column_id != "#2":
            return

        x, y, width, height = self.generation_list_view.bbox(item_id, column_id)

        current_value = self.generation_list_view.item(item_id, "values")[1]
        entry = ttk.Entry(self.generation_list_view)
        entry.place(x=x, y=y, width=width, height=height)
        entry.insert(0, current_value)
        entry.focus_set()

        entry.bind(
            "<FocusOut>",
            lambda e: self.save_edited_quantity(e, entry, item_id),
        )
        entry.bind(
            "<Return>",
            lambda e: self.save_edited_quantity(e, entry, item_id),
        )

    def save_edited_quantity(self, event, entry_widget, item_id):
        new_value_str = entry_widget.get()

        try:
            new_quantity = int(new_value_str)
            if new_quantity <= 0:
                raise ValueError("Количество должно быть положительным")

            filename = self.generation_list_view.item(item_id, "values")[0]

            if filename in self.selected_for_generation:
                self.selected_for_generation[filename] = new_quantity
                self.app.update_status(f"Количество для '{filename}' обновлено")

            self.update_generation_list_view()

        except ValueError:
            messagebox.showerror(
                "Ошибка ввода", "Количество должно быть целым положительным числом."
            )
        finally:
            entry_widget.destroy()

    def on_drag_start(self, event):
        column_id = self.generation_list_view.identify_column(event.x)
        if column_id == "#3":
            self.handle_list_click(event)
            return "break"

        if self.generation_list_view.identify_row(event.y):
            self.generation_list_view.selection_set(
                self.generation_list_view.identify_row(event.y)
            )

    def on_drag_motion(self, event):
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
        new_order = self.generation_list_view.get_children()
        new_selected = {
            self.generation_list_view.item(item, "values")[0]: self.selected_for_generation[
                self.generation_list_view.item(item, "values")[0]
            ]
            for item in new_order
        }
        self.selected_for_generation = new_selected
        self.app.update_status("Порядок элементов изменен")

    def process_generation(self):
        selected_barcodes = self.selected_for_generation

        if not selected_barcodes:
            messagebox.showwarning(
                "Внимание",
                "Список для генерации пуст. Добавьте хотя бы один штрих-код.",
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF Documents", "*.pdf"), ("All Files", "*.*")],
            title="Сохранить PDF файл как...",
        )

        if not file_path:
            self.app.update_status("Генерация отменена. Готово")
            return

        def task():
            pdf_generator.create_pdf_from_barcodes(
                selected_barcodes,
                self.app.cfg.barcode_dir,
                file_path,
                title=os.path.splitext(os.path.basename(file_path))[0],
                page_settings=self.app.cfg.page_settings.to_dict(),
            )
            return file_path

        def on_done(result):
            messagebox.showinfo(
                "Готово",
                f"PDF-файл успешно создан и сохранен как:\n{os.path.basename(result)}",
            )
            self.app.update_status(
                f"PDF-файл успешно создан: {os.path.basename(result)}"
            )

        def on_error(error):
            messagebox.showerror("Ошибка генерации", f"Произошла ошибка:\n{error}")
            self.app.update_status("Ошибка при генерации PDF. Готово")

        self.app._run_task(task, on_done, on_error, "Генерация PDF...")

    def process_preview(self):
        selected_barcodes = self.selected_for_generation
        if not selected_barcodes:
            messagebox.showwarning("Внимание", "Список для генерации пуст.")
            return

        temp_fd, temp_file_path = tempfile.mkstemp(suffix=".pdf")
        os.close(temp_fd)

        def task():
            pdf_generator.create_pdf_from_barcodes(
                selected_barcodes,
                self.app.cfg.barcode_dir,
                temp_file_path,
                "Preview",
                self.app.cfg.page_settings.to_dict(),
            )
            return temp_file_path

        def on_done(result):
            self.app.update_status("Готово к предпросмотру.")
            preview_window.PDFPreviewWindow(
                self.app, result, self.app.cfg.selected_printer
            )

        def on_error(error):
            if os.path.exists(temp_file_path):
                os.remove(temp_file_path)
            messagebox.showerror(
                "Ошибка", f"Не удалось создать PDF для предпросмотра:\n{error}"
            )

        self.app._run_task(task, on_done, on_error, "Генерация PDF для предпросмотра...")

    def process_printing(self):
        selected_barcodes = self.selected_for_generation
        if not selected_barcodes:
            messagebox.showwarning("Внимание", "Список для генерации пуст.")
            return

        if not self.app.cfg.selected_printer:
            messagebox.showerror(
                "Ошибка печати",
                "Принтер не выбран. Проверьте настройки и наличие принтеров в системе.",
            )
            return

        temp_fd, temp_file_path = tempfile.mkstemp(suffix=".pdf")
        os.close(temp_fd)

        def task():
            pdf_generator.create_pdf_from_barcodes(
                selected_barcodes,
                self.app.cfg.barcode_dir,
                temp_file_path,
                title="Печать штрих-кодов",
                page_settings=self.app.cfg.page_settings.to_dict(),
            )
            win32api.ShellExecute(
                0,
                "printto",
                temp_file_path,
                f'"{self.app.cfg.selected_printer}"',
                ".",
                0,
            )
            return temp_file_path

        def on_done(result):
            self.app.update_status("Документ отправлен на печать. Готово.")
            messagebox.showinfo("Печать", "Документ отправлен на печать.")

        def on_error(error):
            messagebox.showerror("Ошибка", f"Произошла ошибка:\n{error}")
            self.app.update_status("Ошибка при печати. Готово.")

        self.app._run_task(task, on_done, on_error, "Генерация и отправка на печать...")
