from __future__ import annotations

import os
import tkinter as tk
from tkinter import messagebox, ttk

import fitz
import win32api


class PDFPreviewWindow(tk.Toplevel):

    def __init__(self, parent, pdf_path: str, selected_printer: str | None):
        super().__init__(parent)
        self.parent = parent
        self.pdf_path = pdf_path
        self.selected_printer = selected_printer
        self.doc = None
        self.current_page = 0
        self.total_pages = 0
        self.photo_image = None

        self.title("Предпросмотр PDF")
        self.geometry("800x600")
        self.transient(parent)
        self.grab_set()

        try:
            self.doc = fitz.open(self.pdf_path)
            self.total_pages = len(self.doc)
        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось открыть PDF-файл:\n{e}", parent=self
            )
            self.destroy()
            return

        self.create_widgets()
        self.load_page()

        self.protocol("WM_DELETE_WINDOW", self.on_close)

    def create_widgets(self):
        nav_frame = ttk.Frame(self)
        nav_frame.pack(fill="x", padx=10, pady=5)

        self.prev_button = ttk.Button(
            nav_frame, text="<< Пред.", command=self.prev_page
        )
        self.prev_button.pack(side="left")

        self.page_label = ttk.Label(nav_frame, text="Страница 1/1", anchor="center")
        self.page_label.pack(side="left", expand=True, fill="x")

        self.next_button = ttk.Button(
            nav_frame, text="След. >>", command=self.next_page
        )
        self.next_button.pack(side="left")

        print_button = ttk.Button(nav_frame, text="Печать", command=self.print_pdf)
        print_button.pack(side="right", padx=(20, 0))

        self.canvas = tk.Canvas(self, bg="gray")
        self.canvas.pack(fill="both", expand=True)

    def load_page(self):
        if not self.doc:
            return

        page = self.doc.load_page(self.current_page)
        pix = page.get_pixmap()
        img_data = pix.tobytes("ppm")
        self.photo_image = tk.PhotoImage(data=img_data)

        self.canvas.create_image(0, 0, anchor="nw", image=self.photo_image)

        self.page_label.config(
            text=f"Страница {self.current_page + 1}/{self.total_pages}"
        )
        self.prev_button.config(state="normal" if self.current_page > 0 else "disabled")
        self.next_button.config(
            state="normal" if self.current_page < self.total_pages - 1 else "disabled"
        )

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_page()

    def next_page(self):
        if self.current_page < self.total_pages - 1:
            self.current_page += 1
            self.load_page()

    def print_pdf(self):
        if not self.selected_printer:
            messagebox.showerror("Ошибка печати", "Принтер не выбран.", parent=self)
            return

        try:
            win32api.ShellExecute(
                0, "printto", self.pdf_path, f'"{self.selected_printer}"', ".", 0
            )
            messagebox.showinfo("Печать", "Документ отправлен на печать.", parent=self)
            self.on_close()
        except Exception as e:
            messagebox.showerror(
                "Ошибка", f"Не удалось отправить на печать:\n{e}", parent=self
            )

    def on_close(self):
        if self.doc:
            self.doc.close()
        os.remove(self.pdf_path)
        self.destroy()
