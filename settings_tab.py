from __future__ import annotations

import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import win32print

import config_manager


class SettingsTab(ttk.Frame):

    def __init__(self, parent: ttk.Notebook, app):
        super().__init__(parent)
        self.app = app
        self.create_widgets()

    def create_widgets(self):
        image_path_frame = ttk.LabelFrame(
            self, text="Путь к изображениям", padding=15
        )
        image_path_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(image_path_frame, text="Папка со штрих-кодами:").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        self.path_entry = ttk.Entry(image_path_frame, width=70)
        self.path_entry.insert(0, self.app.cfg.barcode_dir)
        self.path_entry.config(state="readonly")
        self.path_entry.grid(row=1, column=0, sticky="ew", in_=image_path_frame)

        browse_button = ttk.Button(
            image_path_frame, text="Выбрать...", command=self.select_barcode_dir
        )
        browse_button.grid(row=1, column=1, sticky="w", padx=(10, 0), in_=image_path_frame)

        image_path_frame.columnconfigure(0, weight=1)

        pdf_path_frame = ttk.LabelFrame(
            self, text="Путь к PDF-файлам для ленты", padding=15
        )
        pdf_path_frame.pack(fill="x", padx=10, pady=5)

        ttk.Label(pdf_path_frame, text="Папка с PDF-файлами:").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )
        self.pdf_path_entry = ttk.Entry(pdf_path_frame, width=70)
        self.pdf_path_entry.insert(0, self.app.cfg.pdf_source_dir)
        self.pdf_path_entry.config(state="readonly")
        self.pdf_path_entry.grid(row=1, column=0, sticky="ew")

        pdf_browse_button = ttk.Button(
            pdf_path_frame, text="Выбрать...", command=self.select_pdf_source_dir
        )
        pdf_browse_button.grid(row=1, column=1, sticky="w", padx=(10, 0))
        pdf_path_frame.columnconfigure(0, weight=1)

        printer_frame = ttk.LabelFrame(self, text="Настройки печати", padding=15)
        printer_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(printer_frame, text="Принтер:").grid(
            row=0, column=0, sticky="w", pady=(0, 5)
        )

        self.printer_selector = ttk.Combobox(printer_frame, state="readonly", width=68)
        self.printer_selector.grid(row=1, column=0, sticky="ew")
        self.printer_selector.bind("<<ComboboxSelected>>", self.on_printer_select)

        printer_frame.columnconfigure(0, weight=1)
        self.load_printers()

        page_settings_frame = ttk.LabelFrame(
            self, text="Настройки страницы (мм)", padding=15
        )
        page_settings_frame.pack(fill="x", padx=10, pady=10)

        ttk.Label(page_settings_frame, text="Верхнее:").grid(
            row=0, column=0, sticky="w"
        )
        self.margin_top_entry = ttk.Entry(page_settings_frame, width=10)
        self.margin_top_entry.grid(row=0, column=1, sticky="w", padx=5)
        self.margin_top_entry.insert(0, str(self.app.cfg.page_settings.margin_top))

        ttk.Label(page_settings_frame, text="Нижнее:").grid(
            row=0, column=2, sticky="w", padx=(10, 0)
        )
        self.margin_bottom_entry = ttk.Entry(page_settings_frame, width=10)
        self.margin_bottom_entry.grid(row=0, column=3, sticky="w", padx=5)
        self.margin_bottom_entry.insert(0, str(self.app.cfg.page_settings.margin_bottom))

        ttk.Label(page_settings_frame, text="Левое:").grid(
            row=1, column=0, sticky="w", pady=(5, 0)
        )
        self.margin_left_entry = ttk.Entry(page_settings_frame, width=10)
        self.margin_left_entry.grid(row=1, column=1, sticky="w", padx=5, pady=(5, 0))
        self.margin_left_entry.insert(0, str(self.app.cfg.page_settings.margin_left))

        ttk.Label(page_settings_frame, text="Правое:").grid(
            row=1, column=2, sticky="w", padx=(10, 0), pady=(5, 0)
        )
        self.margin_right_entry = ttk.Entry(page_settings_frame, width=10)
        self.margin_right_entry.grid(row=1, column=3, sticky="w", padx=5, pady=(5, 0))
        self.margin_right_entry.insert(0, str(self.app.cfg.page_settings.margin_right))

        ttk.Label(page_settings_frame, text="Ориентация:").grid(
            row=2, column=0, sticky="w", pady=(10, 0)
        )
        self.orientation_selector = ttk.Combobox(
            page_settings_frame,
            state="readonly",
            values=list(config_manager.PageSettings.ORIENTATIONS),
        )
        self.orientation_selector.grid(
            row=2, column=1, columnspan=3, sticky="ew", pady=(10, 0)
        )
        self.orientation_selector.set(self.app.cfg.page_settings.orientation)

        self.margin_top_entry.bind("<FocusOut>", self.on_page_settings_change)
        self.margin_bottom_entry.bind("<FocusOut>", self.on_page_settings_change)
        self.margin_left_entry.bind("<FocusOut>", self.on_page_settings_change)
        self.margin_right_entry.bind("<FocusOut>", self.on_page_settings_change)
        self.orientation_selector.bind(
            "<<ComboboxSelected>>", self.on_page_settings_change
        )

    def on_page_settings_change(self, event=None):
        try:
            self.app.cfg.page_settings.margin_top = int(self.margin_top_entry.get())
            self.app.cfg.page_settings.margin_bottom = int(self.margin_bottom_entry.get())
            self.app.cfg.page_settings.margin_left = int(self.margin_left_entry.get())
            self.app.cfg.page_settings.margin_right = int(self.margin_right_entry.get())
            self.app.cfg.page_settings.orientation = self.orientation_selector.get()
            self.app.save_config()
            self.app.update_status("Настройки страницы сохранены.")
        except ValueError:
            messagebox.showerror(
                "Ошибка ввода", "Значения полей должны быть целыми числами."
            )

    def load_printers(self):
        printers = [
            p[2]
            for p in win32print.EnumPrinters(
                win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
            )
        ]
        self.printer_selector["values"] = printers
        if self.app.cfg.selected_printer in printers:
            self.printer_selector.set(self.app.cfg.selected_printer)
        elif printers:
            self.printer_selector.current(0)
            self.app.cfg.selected_printer = self.printer_selector.get()

    def on_printer_select(self, event=None):
        self.app.cfg.selected_printer = self.printer_selector.get()
        self.app.save_config()
        self.app.update_status(
            f"Принтер по умолчанию изменен на: {self.app.cfg.selected_printer}"
        )

    def select_barcode_dir(self):
        new_dir = filedialog.askdirectory(
            title="Выберите папку со штрих-кодами",
            initialdir=self.app.cfg.barcode_dir,
        )

        if new_dir and new_dir != self.app.cfg.barcode_dir:
            self.app.cfg.barcode_dir = new_dir
            self.app.update_status(f"Новый путь: {self.app.cfg.barcode_dir}")

            self.path_entry.config(state="normal")
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, self.app.cfg.barcode_dir)
            self.path_entry.config(state="readonly")

            self.app.save_config()
            self.app.load_barcode_list()

    def select_pdf_source_dir(self):
        new_dir = filedialog.askdirectory(
            title="Выберите папку с PDF-файлами",
            initialdir=self.app.cfg.pdf_source_dir,
        )

        if new_dir and new_dir != self.app.cfg.pdf_source_dir:
            self.app.cfg.pdf_source_dir = new_dir
            self.app.update_status(f"Новый путь для PDF: {self.app.cfg.pdf_source_dir}")

            self.pdf_path_entry.config(state="normal")
            self.pdf_path_entry.delete(0, tk.END)
            self.pdf_path_entry.insert(0, self.app.cfg.pdf_source_dir)
            self.pdf_path_entry.config(state="readonly")

            self.app.save_config()
            self.app.ribbon_tab.load_pdf_list()
