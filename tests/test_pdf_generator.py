from __future__ import annotations

import os

import fitz
import pytest
from PIL import Image

from config_manager import AppConfig, PageSettings
from pdf_generator import create_pdf_from_barcodes, merge_pdfs


@pytest.fixture
def barcode_images(tmp_path: str) -> str:
    source_dir = tmp_path / "barcodes"
    source_dir.mkdir()

    img1_path = source_dir / "barcode1.png"
    img2_path = source_dir / "barcode2.png"

    Image.new("RGB", (100, 50), color="red").save(img1_path)
    Image.new("RGB", (100, 50), color="blue").save(img2_path)

    return str(source_dir)


@pytest.fixture
def pdf_files(tmp_path: str) -> str:
    source_dir = tmp_path / "pdfs"
    source_dir.mkdir()

    for name in ["doc1.pdf", "doc2.pdf"]:
        doc = fitz.open()
        page = doc.new_page()
        page.insert_text((50, 50), f"Test {name}")
        doc.save(str(source_dir / name))
        doc.close()

    return str(source_dir)


class TestCreatePdfFromBarcodes:
    def test_success(self, barcode_images: str, tmp_path: str):
        output_path = str(tmp_path / "output.pdf")
        selected_barcodes = {"barcode1.png": 2, "barcode2.png": 1}

        create_pdf_from_barcodes(
            selected_barcodes=selected_barcodes,
            source_dir=barcode_images,
            output_path=output_path,
            title="Test PDF",
        )

        assert os.path.exists(output_path)
        assert os.path.getsize(output_path) > 0

    def test_no_images_found(self, tmp_path: str):
        output_path = str(tmp_path / "output.pdf")
        source_dir = str(tmp_path / "empty_barcodes")
        os.mkdir(source_dir)

        selected_barcodes = {"non_existent_barcode.png": 1}

        with pytest.raises(ValueError, match="Не найдено ни одного файла для размещения в PDF."):
            create_pdf_from_barcodes(
                selected_barcodes=selected_barcodes,
                source_dir=source_dir,
                output_path=output_path,
            )

    def test_landscape_orientation(self, barcode_images: str, tmp_path: str):
        output_path = str(tmp_path / "landscape.pdf")
        selected_barcodes = {"barcode1.png": 1}

        create_pdf_from_barcodes(
            selected_barcodes=selected_barcodes,
            source_dir=barcode_images,
            output_path=output_path,
            page_settings={"orientation": "Альбомная"},
        )

        doc = fitz.open(output_path)
        page = doc[0]
        width, height = page.rect.width, page.rect.height
        assert width > height
        doc.close()

    def test_portrait_orientation(self, barcode_images: str, tmp_path: str):
        output_path = str(tmp_path / "portrait.pdf")
        selected_barcodes = {"barcode1.png": 1}

        create_pdf_from_barcodes(
            selected_barcodes=selected_barcodes,
            source_dir=barcode_images,
            output_path=output_path,
        )

        doc = fitz.open(output_path)
        page = doc[0]
        width, height = page.rect.width, page.rect.height
        assert height > width
        doc.close()


class TestMergePdfs:
    def test_success(self, pdf_files: str, tmp_path: str):
        output_path = str(tmp_path / "merged.pdf")
        selected_pdfs = {"doc1.pdf": 1, "doc2.pdf": 2}

        merge_pdfs(
            selected_pdfs=selected_pdfs,
            source_dir=pdf_files,
            output_path=output_path,
        )

        assert os.path.exists(output_path)
        doc = fitz.open(output_path)
        assert len(doc) == 3
        doc.close()

    def test_no_pdfs_found(self, tmp_path: str):
        output_path = str(tmp_path / "merged.pdf")
        source_dir = str(tmp_path / "empty_pdfs")
        os.mkdir(source_dir)

        with pytest.raises(ValueError, match="Не найдено ни одного PDF-файла для объединения."):
            merge_pdfs(
                selected_pdfs={"nonexistent.pdf": 1},
                source_dir=source_dir,
                output_path=output_path,
            )


class TestAppConfig:
    def test_load_defaults_when_no_file(self):
        config = AppConfig.load("nonexistent_config.ini")
        assert config.barcode_dir == "barcode_images"
        assert config.pdf_source_dir == "pdf_barcodes"
        assert config.selected_printer is None
        assert config.ribbon_printer is None
        assert config.page_settings.margin_top == 25

    def test_save_and_load_roundtrip(self, tmp_path: str):
        config_path = str(tmp_path / "test_config.ini")
        original = AppConfig(
            barcode_dir="/test/barcodes",
            pdf_source_dir="/test/pdfs",
            selected_printer="Test Printer",
            ribbon_printer="Ribbon Printer",
            page_settings=PageSettings(
                margin_top=15, margin_bottom=5, margin_left=20, margin_right=20, orientation="Альбомная"
            ),
        )
        original.save(config_path)

        loaded = AppConfig.load(config_path)
        assert loaded.barcode_dir == original.barcode_dir
        assert loaded.pdf_source_dir == original.pdf_source_dir
        assert loaded.selected_printer == original.selected_printer
        assert loaded.ribbon_printer == original.ribbon_printer
        assert loaded.page_settings == original.page_settings

    def test_validate_valid_config(self):
        config = AppConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_margins(self):
        config = AppConfig(page_settings=PageSettings(margin_top=-5, margin_bottom=100))
        errors = config.validate()
        assert len(errors) == 2

    def test_validate_invalid_orientation(self):
        config = AppConfig(page_settings=PageSettings(orientation="Invalid"))
        errors = config.validate()
        assert len(errors) == 1
        assert "Orientation" in errors[0]
