import os
import pytest
from PIL import Image

# Импортируем тестируемую функцию из вашего проекта
from pdf_generator import create_pdf_from_barcodes


@pytest.fixture
def barcode_images(tmp_path):
    """
    Фикстура pytest для создания временной папки с тестовыми изображениями.
    tmp_path - это встроенная фикстура pytest, которая предоставляет временную директорию.
    """
    source_dir = tmp_path / "barcodes"
    source_dir.mkdir()

    # Создаем два "пустых" файла-изображения для тестов
    img1_path = source_dir / "barcode1.png"
    img2_path = source_dir / "barcode2.png"

    Image.new('RGB', (100, 50), color = 'red').save(img1_path)
    Image.new('RGB', (100, 50), color = 'blue').save(img2_path)

    return str(source_dir)


def test_create_pdf_from_barcodes_success(barcode_images, tmp_path):
    """
    Тест на успешное создание PDF-файла.
    """
    output_path = str(tmp_path / "output.pdf")
    selected_barcodes = {"barcode1.png": 2, "barcode2.png": 1}

    # Вызываем тестируемую функцию
    create_pdf_from_barcodes(
        selected_barcodes=selected_barcodes,
        source_dir=barcode_images,
        output_path=output_path,
        title="Test PDF"
    )

    # Проверяем, что PDF-файл был создан
    assert os.path.exists(output_path), "PDF-файл должен быть создан"
    # Проверяем, что файл не пустой
    assert os.path.getsize(output_path) > 0, "PDF-файл не должен быть пустым"


def test_create_pdf_from_barcodes_no_images_found(tmp_path):
    """
    Тест на выбрасывание исключения, если ни один из файлов не найден.
    """
    output_path = str(tmp_path / "output.pdf")
    # Пустая папка с исходниками
    source_dir = str(tmp_path / "empty_barcodes")
    os.mkdir(source_dir)

    selected_barcodes = {"non_existent_barcode.png": 1}

    # Проверяем, что функция выбрасывает ValueError с определенным сообщением
    with pytest.raises(ValueError, match="Не найдено ни одного файла для размещения в PDF."):
        create_pdf_from_barcodes(
            selected_barcodes=selected_barcodes,
            source_dir=source_dir,
            output_path=output_path
        )
