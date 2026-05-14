from __future__ import annotations

import configparser
import os
from dataclasses import dataclass, field
from typing import Optional

CONFIG_FILE = "config.ini"


@dataclass
class PageSettings:
    margin_top: int = 25
    margin_bottom: int = 10
    margin_left: int = 10
    margin_right: int = 10
    orientation: str = "Книжная"

    ORIENTATIONS = ("Книжная", "Альбомная")

    def to_dict(self) -> dict:
        return {
            "margins": {
                "top": self.margin_top,
                "bottom": self.margin_bottom,
                "left": self.margin_left,
                "right": self.margin_right,
            },
            "orientation": self.orientation,
        }


@dataclass
class AppConfig:
    barcode_dir: str = "barcode_images"
    pdf_source_dir: str = "pdf_barcodes"
    selected_printer: Optional[str] = None
    page_settings: PageSettings = field(default_factory=PageSettings)

    @classmethod
    def load(cls, config_path: str = CONFIG_FILE) -> AppConfig:
        if not os.path.exists(config_path):
            return cls()

        parser = configparser.ConfigParser()
        parser.read(config_path, encoding="utf-8")

        barcode_dir = parser.get("Settings", "BarcodeDir", fallback="barcode_images")
        pdf_source_dir = parser.get("Settings", "PdfSourceDir", fallback="pdf_barcodes")
        selected_printer = parser.get("Settings", "SelectedPrinter", fallback=None) or None

        page_settings = PageSettings(
            margin_top=parser.getint("PageSettings", "MarginTop", fallback=25),
            margin_bottom=parser.getint("PageSettings", "MarginBottom", fallback=10),
            margin_left=parser.getint("PageSettings", "MarginLeft", fallback=10),
            margin_right=parser.getint("PageSettings", "MarginRight", fallback=10),
            orientation=parser.get("PageSettings", "Orientation", fallback="Книжная"),
        )

        return cls(
            barcode_dir=barcode_dir,
            pdf_source_dir=pdf_source_dir,
            selected_printer=selected_printer,
            page_settings=page_settings,
        )

    def save(self, config_path: str = CONFIG_FILE) -> None:
        parser = configparser.ConfigParser()
        parser["Settings"] = {
            "BarcodeDir": self.barcode_dir,
            "PdfSourceDir": self.pdf_source_dir,
            "SelectedPrinter": self.selected_printer or "",
        }
        parser["PageSettings"] = {
            "MarginTop": str(self.page_settings.margin_top),
            "MarginBottom": str(self.page_settings.margin_bottom),
            "MarginLeft": str(self.page_settings.margin_left),
            "MarginRight": str(self.page_settings.margin_right),
            "Orientation": self.page_settings.orientation,
        }
        with open(config_path, "w", encoding="utf-8") as f:
            parser.write(f)

    def validate(self) -> list[str]:
        errors: list[str] = []
        ps = self.page_settings

        if ps.margin_top < 0 or ps.margin_top > 50:
            errors.append(f"MarginTop ({ps.margin_top}) вне допустимого диапазона 0-50 мм")
        if ps.margin_bottom < 0 or ps.margin_bottom > 50:
            errors.append(f"MarginBottom ({ps.margin_bottom}) вне допустимого диапазона 0-50 мм")
        if ps.margin_left < 0 or ps.margin_left > 50:
            errors.append(f"MarginLeft ({ps.margin_left}) вне допустимого диапазона 0-50 мм")
        if ps.margin_right < 0 or ps.margin_right > 50:
            errors.append(f"MarginRight ({ps.margin_right}) вне допустимого диапазона 0-50 мм")
        if ps.orientation not in PageSettings.ORIENTATIONS:
            errors.append(f"Orientation '{ps.orientation}' недопустима. Допустимые: {PageSettings.ORIENTATIONS}")

        return errors
