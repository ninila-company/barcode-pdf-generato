# Устанавливаем кодировку вывода в UTF-8 для корректной работы с кириллицей
$OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "===================================" -ForegroundColor Green
Write-Host "  Сборка приложения CodeOZON..." -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green

# --- Параметры ---
$ScriptName = "gui.py"
$ExeName = "CodeOZON"
$IconFile = "app_icon.ico"

# --- Очистка ---
Write-Host ""
Write-Host "Очистка предыдущих сборок..." -ForegroundColor Yellow

# Удаляем старые артефакты сборки, если они существуют
if (Test-Path "$ExeName.spec") {
    Remove-Item "$ExeName.spec"
    Write-Host "Удален файл: $ExeName.spec"
}
if (Test-Path "dist") {
    Remove-Item -Path "dist" -Recurse -Force
    Write-Host "Удалена папка: dist"
}
if (Test-Path "build") {
    Remove-Item -Path "build" -Recurse -Force
    Write-Host "Удалена папка: build"
}
Write-Host "Очистка завершена." -ForegroundColor Green

# --- Запуск PyInstaller ---
Write-Host ""
Write-Host "Запуск PyInstaller..." -ForegroundColor Yellow

# Собираем аргументы для PyInstaller. Это делает команду более читаемой.
$pyinstallerArgs = @(
    "--onefile",
    "--windowed",
    "--name", $ExeName,
    "--icon", $IconFile,
    "--add-data", "barcode_images;barcode_images",
    "--add-data", "C:\Windows\Fonts\Verdana.ttf;.",
    "--hidden-import", "fitz.impl",
    $ScriptName
)

pyinstaller $pyinstallerArgs

# --- Проверка результата ---
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "!!! ОШИБКА: Сборка не удалась. Проверьте сообщения выше." -ForegroundColor Red
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Write-Host ""
Write-Host "===================================" -ForegroundColor Green
Write-Host "  Сборка успешно завершена!" -ForegroundColor Green
Write-Host "===================================" -ForegroundColor Green
Write-Host ""
Write-Host "Готовый файл $($ExeName).exe находится в папке: dist"
Write-Host ""
Read-Host "Нажмите Enter для выхода"
