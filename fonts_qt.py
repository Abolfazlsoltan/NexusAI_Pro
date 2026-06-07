"""
fonts_qt.py — بارگذاری و مدیریت فونت وزیر در PyQt

ویژگی‌ها:
    - تلاش برای بارگذاری فونت وزیر از مسیر سیستم یا پوشه‌ی مجازی
    - در صورت عدم وجود، بدون خطا ادامه می‌دهد
    - سازگار با محیط‌های توسعه و بسته‌بندی
"""

from __future__ import annotations

import sys
from pathlib import Path
from PyQt6.QtGui import QFontDatabase


def load_vazir() -> bool:
    """
    تلاش برای یافتن و بارگذاری فونت Vazir.
    اولویت با فونت نصبی در سیستم است، سپس فایل محلی.
    بازگشت True در صورت موفقیت.
    """
    # مسیرهای احتمالی فونت وزیر
    possible_paths = [
        # فونت کنار اسکریپت
        Path(__file__).parent / "Vazir.ttf",
        Path(__file__).parent / "fonts" / "Vazir.ttf",
        # مسیر سیستم (لینوکس)
        Path.home() / ".local" / "share" / "fonts" / "Vazir.ttf",
        Path.home() / ".fonts" / "Vazir.ttf",
        # مسیرهای معمول ویندوز
        Path("C:/Windows/Fonts/Vazir.ttf"),
        # مسیرهای عمومی لینوکس
        Path("/usr/share/fonts/truetype/vazir/Vazir.ttf"),
        Path("/usr/local/share/fonts/Vazir.ttf"),
    ]

    for font_path in possible_paths:
        if font_path.exists():
            try:
                QFontDatabase.addApplicationFont(str(font_path))
                return True
            except Exception:
                continue
    return False


# در صورت نیاز به فهرست خانواده‌ها (برای عیب‌یابی)
def available_families() -> list[str]:
    return QFontDatabase().families()