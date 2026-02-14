from tkinter import ttk


def setup_styles(style: ttk.Style):
    """
    Настраивает пользовательские стили для ttk виджетов и возвращает палитру.
    """
    style.theme_use("clam")  # Современная тема как основа

    # --- Цветовая палитра ---
    colors = {
        "BG_COLOR": "#2E2E2E",  # Темно-серый фон
        "FG_COLOR": "#EAEAEA",  # Светлый текст
        "FRAME_BG": "#3C3C3C",  # Фон для рамок
        "ACCENT_COLOR": "#007ACC",  # Синий акцент
        "ACCENT_ACTIVE": "#005F9E",  # Синий при наведении/нажатии
        "SUCCESS_COLOR": "#28A745",  # Зеленый для успеха
        "SUCCESS_ACTIVE": "#218838",
        "DANGER_COLOR": "#DC3545",  # Красный для опасности
        "DANGER_ACTIVE": "#C82333",
        "LIST_HEADER_BG": "#4A4A4A",
        "LIST_BG": "#555555",
        "LIST_SELECT_BG": "#007ACC",
    }

    # --- Общие настройки ---
    style.configure(".", background=colors["BG_COLOR"], foreground=colors["FG_COLOR"], font=("Verdana", 9))
    style.configure("TFrame", background=colors["BG_COLOR"])
    style.configure("TLabel", background=colors["BG_COLOR"], foreground=colors["FG_COLOR"])
    style.configure("TLabelFrame", background=colors["BG_COLOR"], borderwidth=1, relief="solid")
    style.configure("TLabelFrame.Label", background=colors["BG_COLOR"], foreground=colors["FG_COLOR"])
    style.configure("TEntry", fieldbackground=colors["LIST_BG"], foreground=colors["FG_COLOR"], insertcolor=colors["FG_COLOR"])
    style.configure("TCombobox", fieldbackground=colors["LIST_BG"], foreground=colors["FG_COLOR"], selectbackground=colors["FRAME_BG"])
    style.map("TCombobox", fieldbackground=[("readonly", colors["FRAME_BG"])])

    # --- Стили кнопок ---
    style.configure("TButton", padding=6, relief="flat", font=("Verdana", 10, "bold"))
    style.map("TButton", foreground=[("!disabled", "white")], background=[("!disabled", colors["ACCENT_COLOR"]), ("active", colors["ACCENT_ACTIVE"])])

    style.configure("Success.TButton", background=colors["SUCCESS_COLOR"])
    style.map("Success.TButton", background=[("active", colors["SUCCESS_ACTIVE"])])

    style.configure("Danger.TButton", background=colors["DANGER_COLOR"])
    style.map("Danger.TButton", background=[("active", colors["DANGER_ACTIVE"])])

    # Стили для Treeview
    style.configure("Treeview", background=colors["LIST_BG"], fieldbackground=colors["LIST_BG"], foreground=colors["FG_COLOR"])
    style.configure("Treeview.Heading", background=colors["LIST_HEADER_BG"], foreground=colors["FG_COLOR"], font=("Verdana", 10, "bold"))
    style.map("Treeview", background=[("selected", colors["LIST_SELECT_BG"])])
    style.map("Treeview.Heading", background=[("active", colors["ACCENT_ACTIVE"])])

    # Стили для Scrollbar
    style.configure("Vertical.TScrollbar", background=colors["FRAME_BG"], troughcolor=colors["BG_COLOR"], bordercolor=colors["BG_COLOR"], arrowcolor=colors["FG_COLOR"])
    style.map("Vertical.TScrollbar", background=[("active", colors["ACCENT_COLOR"])])

    return colors
