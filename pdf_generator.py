import os
from typing import Optional

from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas


def create_pdf_from_barcodes(
    selected_barcodes: dict,
    source_dir: str,
    output_path: str,
    title: Optional[str] = None,
    page_settings: Optional[dict] = None,
):
    """
    Основная функция, реализующая ядро приложения.

    1.  Сбор данных: Принимает словарь {имя_файла: количество} и путь к исходным файлам.
    2.  Размещение на PDF: Раскладывает изображения по сетке на страницах A4, разделяя группы линией.
    3.  Сохранение: Сохраняет итоговый PDF.
    """
    # Получаем список всех путей к файлам, которые существуют
    existing_image_paths = [
        os.path.join(source_dir, f)
        for f in selected_barcodes.keys()
        if os.path.exists(os.path.join(source_dir, f))
    ]

    if not existing_image_paths:
        raise ValueError("Не найдено ни одного файла для размещения в PDF.")

    # --- Регистрация шрифта с поддержкой кириллицы ---
    # Стандартные шрифты (Helvetica) не поддерживают кириллицу.
    # Регистрируем шрифт Verdana, который обычно есть в Windows.
    try:
        # Имя 'Verdana' - это внутренний идентификатор для reportlab
        # 'Verdana.ttf' - имя файла шрифта в системе
        pdfmetrics.registerFont(TTFont("Verdana", "Verdana.ttf"))
        font_name = "Verdana"
    except Exception:
        # Если Verdana не найден, возвращаемся к стандартному, но кириллица не будет работать
        font_name = "Helvetica"

    # --- Размещение изображений на PDF-странице ---
    # Настройки страницы
    if page_settings is None:
        page_settings = {}

    orientation = page_settings.get("orientation", "Книжная")
    margins = page_settings.get(
        "margins", {"top": 25, "bottom": 10, "left": 10, "right": 10}
    )

    page_size = landscape(A4) if orientation == "Альбомная" else A4

    print("Создание PDF документа...")
    c = canvas.Canvas(output_path, pagesize=page_size)
    page_width, page_height = page_size  # Размеры страницы в пунктах (points)

    doc_title = title if title else os.path.splitext(os.path.basename(output_path))[0]

    def draw_page_header(canvas_obj):
        """Рисует заголовок вверху страницы."""
        canvas_obj.setFont(font_name, 12)
        canvas_obj.drawCentredString(
            page_width / 2.0, page_height - margins["top"] * mm + 10 * mm, doc_title
        )

    draw_page_header(c)  # Рисуем заголовок на первой странице

    # Задаем размеры и отступы в миллиметрах и конвертируем в пункты
    img_draw_width = 45 * mm
    margin_left = margins["left"] * mm
    margin_right = margins["right"] * mm
    margin_top = margins["top"] * mm
    margin_bottom = margins["bottom"] * mm
    gap_x = 2 * mm
    gap_y = 5 * mm

    # Определяем высоту изображения, сохраняя пропорции, чтобы избежать искажений
    # Мы делаем это один раз на основе первого изображения в списке
    with Image.open(existing_image_paths[0]) as img:
        img_width_px, img_height_px = img.size
    aspect_ratio = img_height_px / img_width_px
    img_draw_height = img_draw_width * aspect_ratio

    # Начальные координаты для первого изображения (левый верхний угол, с учетом отступов)
    x = margin_left
    y = page_height - margin_top - img_draw_height

    barcode_types = list(selected_barcodes.keys())
    for i, filename in enumerate(barcode_types):
        quantity = selected_barcodes[filename]
        full_path = os.path.join(source_dir, filename)

        if not os.path.exists(full_path):
            print(f"Warning: File not found and will be skipped: {full_path}")
            continue

        # Размещаем все экземпляры текущего типа штрих-кода
        for _ in range(quantity):
            # Проверяем, не выходим ли за правый край страницы
            if x + img_draw_width > page_width - margin_right:
                # Переходим на новую строку
                x = margin_left
                y -= img_draw_height + gap_y

            # Проверяем, не выходим ли за нижний край страницы
            if y < margin_bottom:
                c.showPage()  # Завершаем текущую страницу
                draw_page_header(c)  # Рисуем заголовок на новой странице
                # Сбрасываем координаты для новой страницы
                x = margin_left
                y = page_height - margin_top - img_draw_height

            # Рисуем изображение на холсте PDF
            c.drawImage(full_path, x, y, width=img_draw_width, height=img_draw_height)

            # Сдвигаем координату X для следующего изображения в ряду
            x += img_draw_width + gap_x

        # --- Рисуем разделительную линию после каждой группы (кроме последней) ---
        is_last_group = i == len(barcode_types) - 1
        if not is_last_group:
            # Если группа закончилась не в начале строки, принудительно переходим на новую
            if x != margin_left:
                x = margin_left
                y -= img_draw_height + gap_y

            # Проверяем, не нужно ли перейти на новую страницу перед отрисовкой линии
            if y < margin_bottom:
                c.showPage()
                y = page_height - margin_top - img_draw_height
                continue  # Не рисуем линию в самом верху новой страницы

            # Рисуем линию в промежутке между строками
            line_y_pos = y + img_draw_height + (gap_y / 2)
            c.setStrokeColorRGB(0.7, 0.7, 0.7)  # Светло-серый цвет
            c.setLineWidth(0.5)
            c.line(margin_left, line_y_pos, page_width - margin_right, line_y_pos)

    # --- Сохранение ---
    print("Сохранение PDF...")
    c.save()
