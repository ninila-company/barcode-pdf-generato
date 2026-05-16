from __future__ import annotations

import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import win32print

import app_styles
import barcode_selection_tab
import ribbon_barcode_selection_tab
import config_manager
import main_tab
import ribbon_print_tab
import settings_tab


class BarcodePDFApp(tk.Tk):

    def __init__(self):
        super().__init__()

        self.title("Генератор PDF со штрих-кодами")
        self.geometry("850x600")

        self.cfg = config_manager.AppConfig.load()
        if not self.cfg.selected_printer:
            try:
                self.cfg.selected_printer = win32print.GetDefaultPrinter()
            except RuntimeError:
                self.cfg.selected_printer = None

        self.setup_styles()
        self.create_widgets()
        self.load_barcode_list()

    def setup_styles(self):
        style = ttk.Style(self)
        colors = app_styles.setup_styles(style)
        self.BG_COLOR = colors["BG_COLOR"]
        self.FG_COLOR = colors["FG_COLOR"]
        self.FRAME_BG = colors["FRAME_BG"]

    def save_config(self):
        self.cfg.save()

    def create_widgets(self):
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Выход", command=self.destroy)
        menubar.add_cascade(label="Файл", menu=file_menu)

        help_menu = tk.Menu(menubar, tearoff=0)
        help_menu.add_command(label="О программе", command=self.show_about_dialog)
        menubar.add_cascade(label="Справка", menu=help_menu)

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.main_tab = main_tab.MainTab(self.notebook, self)
        self.selection_tab = barcode_selection_tab.BarcodeSelectionTab(
            self.notebook, self
        )
        self.ribbon_selection_tab = ribbon_barcode_selection_tab.RibbonBarcodeSelectionTab(
            self.notebook, self
        )
        self.ribbon_tab = ribbon_print_tab.RibbonPrintTab(self.notebook, self)
        self.settings_tab = settings_tab.SettingsTab(self.notebook, self)

        self.notebook.add(self.main_tab, text="Печать с листа")
        self.notebook.add(self.selection_tab, text="Выбор штрих-кодов для печати с листа")
        self.notebook.add(self.ribbon_tab, text="Печать с ленты")
        self.notebook.add(self.ribbon_selection_tab, text="Выбор штрих-кодов для печати с ленты")
        self.notebook.add(self.settings_tab, text="Настройки")

        self.status_bar = ttk.Label(
            self, text="Загрузка...", anchor="w", relief=tk.SUNKEN
        )
        self.status_bar.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

    def load_barcode_list(self):
        self.main_tab.clear_list(silent=True)
        self.main_tab.barcode_selector.set("")

        if not os.path.isdir(self.cfg.barcode_dir):
            messagebox.showwarning(
                "Папка не найдена",
                f"Папка '{self.cfg.barcode_dir}' не найдена.\n\n"
                "Пожалуйста, укажите правильный путь на вкладке 'Настройки'.",
            )
            self.main_tab.barcode_selector["values"] = []
            self.main_tab.all_barcode_files = []
            self.update_status("Ошибка: неверный путь к папке со штрих-кодами.")
            return

        barcode_files = sorted(
            f
            for f in os.listdir(self.cfg.barcode_dir)
            if f.lower().endswith((".png", ".jpg", ".jpeg"))
        )

        if not barcode_files:
            messagebox.showwarning(
                "Внимание",
                f"В папке '{self.cfg.barcode_dir}' не найдено изображений.",
            )
            self.main_tab.barcode_selector["values"] = []
            self.main_tab.all_barcode_files = []
            self.update_status("Внимание: Изображения не найдены.")
        else:
            self.main_tab.set_barcodes(barcode_files)
            self.selection_tab.populate_barcodes(barcode_files)
            self.ribbon_tab.load_pdf_list()
            self.ribbon_selection_tab.populate_files(self.ribbon_tab.all_pdf_files)
            self.update_status("Готово")

    def add_barcodes_from_selection_tab(self, checkbox_vars):
        added = self.main_tab.add_barcodes_from_selection(checkbox_vars)
        if added > 0:
            self.update_status(f"Добавлено {added} новых позиций в список.")
        self.main_tab.switch_to_main_tab()

    def add_pdfs_from_ribbon_selection_tab(self, checkbox_vars):
        added = self.ribbon_tab.add_selected_from_selection(checkbox_vars)
        if added > 0:
            self.update_status(f"Добавлено {added} новых позиций в список печати с ленты.")
        self.ribbon_tab.switch_to_self()

    def update_status(self, message):
        self.status_bar.config(text=message)
        self.update_idletasks()

    def _run_task(
        self,
        task: callable,
        on_done: callable,
        on_error: callable,
        status_text: str = "Выполнение...",
    ):
        self.attributes("-disabled", True)
        self.update_status(status_text)
        self.update_idletasks()

        def _wrapper():
            try:
                result = task()
                self.after(
                    0, lambda res=result: self._task_completed(on_done, on_error, res, None)
                )
            except Exception as exc:
                self.after(
                    0, lambda err=exc: self._task_completed(on_done, on_error, None, err)
                )

        threading.Thread(target=_wrapper, daemon=True).start()

    def _task_completed(
        self, on_done: callable, on_error: callable, result, error: Exception | None
    ):
        self.attributes("-disabled", False)
        self.focus_set()
        if error:
            on_error(error)
        else:
            on_done(result)

    def show_about_dialog(self):
        messagebox.showinfo(
            "О программе",
            "Генератор PDF со штрих-кодами\n\n"
            "Версия: 1.1\n\n"
            "Приложение для удобного создания PDF-документов из изображений штрих-кодов.",
        )


if __name__ == "__main__":
    app = BarcodePDFApp()
    app.mainloop()
