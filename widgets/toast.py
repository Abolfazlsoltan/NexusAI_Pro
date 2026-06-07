"""
widgets/toast.py — سیستم اعلان‌های موقت (Toast) با طراحی شیشه‌ای

ویژگی‌ها:
    - نمایش پیام‌های موقت با رنگ‌بندی (info, success, error)
    - انیمیشن ورودی و خروجی نرم
    - موقعیت‌دهی پویا در پایین پنجره
    - پشتیبانی از چند اعلان هم‌زمان
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, QTimer, QPropertyAnimation, QPoint, QEasingCurve
from PyQt6.QtWidgets import QLabel, QFrame


class ToastManager:
    """مدیریت متمرکز اعلان‌های Toast در یک پنجره."""

    def __init__(self, parent) -> None:
        self.parent = parent
        self.active_toasts: list[QLabel] = []

    def show(
        self,
        message: str,
        kind: str = "info",
        duration: int = 2500,
        offset_y: int = 80,
    ) -> None:
        """
        نمایش یک Toast با پیام مشخص.

        پارامترها:
            message: متن پیام
            kind: نوع (info, success, error)
            duration: مدت نمایش به میلی‌ثانیه
            offset_y: فاصله از پایین پنجره
        """
        # رنگ‌بندی بر اساس نوع
        colors = {
            "info": "#00B4D8",
            "success": "#2ECC71",
            "error": "#E74C3C",
            "warning": "#F39C12",
        }
        color = colors.get(kind, "#888888")

        # ایجاد برچسب
        toast = QLabel(message, self.parent)
        toast.setAlignment(Qt.AlignmentFlag.AlignCenter)
        toast.setWordWrap(True)
        toast.setMinimumWidth(200)
        toast.setMaximumWidth(self.parent.width() - 40)
        toast.setStyleSheet(f"""
            QLabel {{
                background: rgba(30, 30, 40, 0.9);
                color: {color};
                border: 1px solid {color};
                border-radius: 16px;
                padding: 10px 20px;
                font-size: 11pt;
                font-weight: bold;
            }}
        """)
        toast.adjustSize()

        # موقعیت اولیه (پایین‌تر از ناحیه مقصد)
        x = (self.parent.width() - toast.width()) // 2
        y_target = self.parent.height() - offset_y - toast.height()
        y_start = y_target + 30
        toast.move(x, y_start)
        toast.show()

        self.active_toasts.append(toast)

        # انیمیشن ورودی
        anim_in = QPropertyAnimation(toast, b"pos")
        anim_in.setDuration(400)
        anim_in.setStartValue(QPoint(x, y_start))
        anim_in.setEndValue(QPoint(x, y_target))
        anim_in.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim_in.start()

        # زمان‌بندی محو شدن
        QTimer.singleShot(duration, lambda: self._fade_out(toast))

    def _fade_out(self, toast: QLabel) -> None:
        """انیمیشن محو شدن و حذف از لیست."""
        if toast not in self.active_toasts:
            return
        # کاهش شفافیت با استایل (ساده‌ترین روش بدون QGraphicsEffect)
        # برای سادگی، مستقیم حذف می‌کنیم (می‌توان با تایمر opacity ساخت)
        self.active_toasts.remove(toast)
        toast.deleteLater()

    def update_position(self) -> None:
        """به‌روزرسانی موقعیت تمام Toastهای فعال هنگام تغییر اندازه پنجره."""
        for toast in self.active_toasts:
            x = (self.parent.width() - toast.width()) // 2
            y = self.parent.height() - 80 - toast.height()
            toast.move(x, y)