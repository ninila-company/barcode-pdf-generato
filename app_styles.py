from tkinter import ttk


def setup_styles(style: ttk.Style):
    """
    Настраивает пользовательские стили для ttk виджетов и возвращает палитру.
    """
    style.theme_use("classic")  # Классическая тема для вида в стиле Windows 95

    # --- Цветовая палитра в стиле Windows 95 ---
    colors = {
        "BG_COLOR": "#C0C0C0",  # Классический серый фон
        "FG_COLOR": "#000000",  # Черный текст
        "FRAME_BG": "#C0C0C0",  # Фон для рамок - такой же, как основной
        "ACCENT_COLOR": "#000080",  # Темно-синий для выделения (Navy)
        "ACCENT_ACTIVE": "#0000A0",  # Чуть светлее синий при наведении
        "SUCCESS_COLOR": "#008000",  # Зеленый
        "SUCCESS_ACTIVE": "#00A000",
        "DANGER_COLOR": "#8B0000",  # Темно-красный
        "DANGER_ACTIVE": "#A52A2A",
        "LIST_HEADER_BG": "#C0C0C0",  # Фон заголовка списка
        "LIST_BG": "#FFFFFF",  # Белый фон для полей ввода и списков
        "LIST_SELECT_BG": "#000080",  # Темно-синий фон при выборе
        "LIST_SELECT_FG": "#FFFFFF",  # Белый текст при выборе
    }

    # --- Общие настройки ---
    style.configure(
        ".",
        background=colors["BG_COLOR"],
        foreground=colors["FG_COLOR"],
        font=("Verdana", 9),
    )
    style.configure("TFrame", background=colors["BG_COLOR"])
    style.configure(
        "TLabel", background=colors["BG_COLOR"], foreground=colors["FG_COLOR"]
    )
    style.configure(
        "TLabelFrame", background=colors["BG_COLOR"], borderwidth=2, relief="groove"
    )
    style.configure(
        "TLabelFrame.Label",
        background=colors["BG_COLOR"],
        foreground=colors["FG_COLOR"],
    )
    style.configure(
        "TEntry",
        fieldbackground=colors["LIST_BG"],
        foreground=colors["FG_COLOR"],
        insertcolor=colors["FG_COLOR"],
        borderwidth=2,
        relief="sunken",
    )
    style.configure(
        "TCombobox",
        fieldbackground=colors["LIST_BG"],
        foreground=colors["FG_COLOR"],
        selectbackground=colors["LIST_SELECT_BG"],
        selectforeground=colors["LIST_SELECT_FG"],
    )
    style.map("TCombobox", fieldbackground=[("readonly", colors["LIST_BG"])])

    # --- Стили кнопок ---
    style.configure(
        "TButton", padding=6, relief="raised", font=("Verdana", 9), borderwidth=2
    )
    style.map(
        "TButton",
        foreground=[("!disabled", colors["FG_COLOR"])],
        background=[("!disabled", colors["BG_COLOR"]), ("active", "#DCDCDC")],
    )

    # Для цветных кнопок оставим цвет фона, но сохраним общий стиль
    style.configure(
        "Success.TButton", background=colors["SUCCESS_COLOR"], foreground="white"
    )
    style.map(
        "Success.TButton",
        background=[("active", colors["SUCCESS_ACTIVE"])],
        foreground=[("!disabled", "white")],
    )

    style.configure(
        "Danger.TButton", background=colors["DANGER_COLOR"], foreground="white"
    )
    style.map(
        "Danger.TButton",
        background=[("active", colors["DANGER_ACTIVE"])],
        foreground=[("!disabled", "white")],
    )

    # Стили для Treeview
    style.configure(
        "Treeview",
        background=colors["LIST_BG"],
        fieldbackground=colors["LIST_BG"],
        foreground=colors["FG_COLOR"],
        relief="sunken",
    )
    style.configure(
        "Treeview.Heading",
        background=colors["LIST_HEADER_BG"],
        foreground=colors["FG_COLOR"],
        font=("Verdana", 9, "bold"),
        relief="raised",
    )
    style.map(
        "Treeview",
        background=[("selected", colors["LIST_SELECT_BG"])],
        foreground=[("selected", colors["LIST_SELECT_FG"])],
    )
    style.map("Treeview.Heading", background=[("active", "#DCDCDC")])

    # Стили для Scrollbar
    style.configure(
        "Vertical.TScrollbar",
        background=colors["FRAME_BG"],
        troughcolor=colors["BG_COLOR"],
        bordercolor=colors["BG_COLOR"],
        arrowcolor=colors["FG_COLOR"],
    )
    style.map("Vertical.TScrollbar", background=[("active", colors["ACCENT_COLOR"])])

    return colors
