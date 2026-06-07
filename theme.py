"""
theme.py — مدیریت تم‌های برنامه با قابلیت سویچ زنده و ۴ پوسته‌ی حرفه‌ای

ویژگی‌ها:
    - ۴ تم کامل: Dark Glass, Cyberpunk, Light Soft, Midnight Azure
    - کلاس C برای دسترسی به تم جاری و سویچ زنده
    - تولید استایل‌شیت سراسری برای QMainWindow
    - پشتیبانی از شنونده‌ها برای بروزرسانی لحظه‌ای
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class Theme:
    """ساختار یک تم با تمام رنگ‌ها و المان‌های لازم."""
    bg: str
    sidebar: str
    text: str
    accent: str
    bubble_user: str
    bubble_bot: str
    input_bg: str
    shadow: str
    radius: str
    font: str


# ── تعریف تم‌ها ───────────────────────────────────────────
THEME_DARK_GLASS = Theme(
    bg="rgba(20, 20, 30, 0.85)",
    sidebar="rgba(25, 25, 35, 0.9)",
    text="#ECEFF4",
    accent="#5E81AC",
    bubble_user="#434C5E",
    bubble_bot="rgba(46, 52, 64, 0.8)",
    input_bg="rgba(30, 30, 40, 0.7)",
    shadow="0 8px 32px rgba(0,0,0,0.3)",
    radius="16px",
    font="Vazir, Segoe UI, sans-serif",
)

THEME_CYBERPUNK = Theme(
    bg="rgba(10, 0, 20, 0.9)",
    sidebar="rgba(20, 0, 40, 0.95)",
    text="#FF66C4",
    accent="#00FFFF",
    bubble_user="#3A0CA3",
    bubble_bot="#240046",
    input_bg="rgba(20, 0, 40, 0.8)",
    shadow="0 0 20px #FF66C4",
    radius="20px",
    font="Vazir, Consolas, monospace",
)

THEME_LIGHT_SOFT = Theme(
    bg="rgba(245, 245, 250, 0.9)",
    sidebar="rgba(235, 235, 240, 0.95)",
    text="#2E3440",
    accent="#5E81AC",
    bubble_user="#D8DEE9",
    bubble_bot="#ECEFF4",
    input_bg="rgba(250, 250, 255, 0.8)",
    shadow="0 4px 16px rgba(0,0,0,0.05)",
    radius="16px",
    font="Vazir, Segoe UI, sans-serif",
)

THEME_MIDNIGHT_AZURE = Theme(
    bg="rgba(15, 25, 45, 0.9)",
    sidebar="rgba(18, 28, 48, 0.95)",
    text="#B8D4F0",
    accent="#00B4D8",
    bubble_user="#1B2A4A",
    bubble_bot="#0F1A30",
    input_bg="rgba(20, 30, 50, 0.8)",
    shadow="0 8px 30px rgba(0,180,216,0.15)",
    radius="18px",
    font="Vazir, Segoe UI, sans-serif",
)

THEMES: dict[str, Theme] = {
    "dark_glass": THEME_DARK_GLASS,
    "cyberpunk": THEME_CYBERPUNK,
    "light_soft": THEME_LIGHT_SOFT,
    "midnight_azure": THEME_MIDNIGHT_AZURE,
}


class C:
    """کلاس دسترسی به تم جاری و مدیریت تغییرات زنده."""

    current_theme: str = "dark_glass"
    _listeners: list[Callable[[str], None]] = []

    @classmethod
    def set_theme(cls, name: str) -> None:
        """تغییر تم و خبر کردن همه‌ی شنونده‌ها."""
        if name in THEMES:
            cls.current_theme = name
            for callback in cls._listeners:
                try:
                    callback(name)
                except Exception:
                    pass

    @classmethod
    def get(cls, key: str) -> str:
        """دریافت یک ویژگی از تم جاری."""
        theme = THEMES.get(cls.current_theme, THEME_DARK_GLASS)
        return getattr(theme, key, "")

    @classmethod
    def add_listener(cls, callback: Callable[[str], None]) -> None:
        """ثبت شنونده برای رویداد تغییر تم."""
        if callback not in cls._listeners:
            cls._listeners.append(callback)

    @classmethod
    def remove_listener(cls, callback: Callable[[str], None]) -> None:
        """حذف شنونده."""
        if callback in cls._listeners:
            cls._listeners.remove(callback)


def apply_global_style() -> str:
    """تولید استایل‌شیت سراسری برای QMainWindow بر اساس تم جاری."""
    t = THEMES.get(C.current_theme, THEME_DARK_GLASS)
    return f"""
    QMainWindow#NexusWindow {{
        background: {t.bg};
        border-radius: {t.radius};
    }}
    QWidget {{
        font-family: {t.font};
        color: {t.text};
    }}
    QComboBox, QPushButton {{
        background: {t.input_bg};
        border: 1px solid {t.accent};
        border-radius: 8px;
        padding: 6px 12px;
        color: {t.text};
    }}
    QComboBox:hover, QPushButton:hover {{
        background: {t.accent};
        color: white;
    }}
    QComboBox::drop-down {{
        subcontrol-origin: padding;
        subcontrol-position: top right;
        width: 20px;
        border-left: 1px solid {t.accent};
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 6px;
    }}
    QScrollBar::handle:vertical {{
        background: {t.accent};
        border-radius: 3px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0px;
    }}
    QTextEdit {{
        background: {t.input_bg};
        border: 1px solid {t.accent};
        border-radius: 12px;
        padding: 8px;
        color: {t.text};
    }}
    QLabel {{
        color: {t.text};
    }}
    """