"""
widgets/input_bar.py — نوار ورودی پیام

ویژگی‌ها:
    - فیلد متنی چندخطی با محدودیت ارتفاع
    - دکمه‌های ارسال و توقف (Abort)
    - ارسال با دکمه Enter (بدون Shift)
    - استایل پویا با تم جاری
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTextEdit, QPushButton
from theme import C


class InputBar(QWidget):
    """نوار پایینی برای ورود و ارسال پیام."""

    send_clicked = pyqtSignal(str)
    abort_requested = pyqtSignal()

    def __init__(
        self,
        on_send=None,
        toast_mgr=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.on_send = on_send
        self.toast_mgr = toast_mgr

        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 10)
        layout.setSpacing(8)

        # فیلد ورودی
        self.input = QTextEdit()
        self.input.setPlaceholderText("پیام خود را بنویسید... (Enter برای ارسال)")
        self.input.setMaximumHeight(120)
        self.input.setTabChangesFocus(True)
        self._apply_input_style()
        layout.addWidget(self.input, 1)

        # دکمه ارسال
        self.send_btn = QPushButton("⬆️")
        self.send_btn.setFixedSize(42, 42)
        self.send_btn.setToolTip("ارسال پیام")
        self.send_btn.clicked.connect(self._emit_send)
        layout.addWidget(self.send_btn)

        # دکمه توقف (Abort)
        self.abort_btn = QPushButton("⏹️")
        self.abort_btn.setFixedSize(42, 42)
        self.abort_btn.setToolTip("توقف تولید پاسخ")
        self.abort_btn.clicked.connect(self.abort_requested)
        self.abort_btn.setVisible(False)
        layout.addWidget(self.abort_btn)

    def _apply_input_style(self) -> None:
        self.input.setStyleSheet(f"""
            QTextEdit {{
                background: {C.get('input_bg')};
                border: 1px solid {C.get('accent')};
                border-radius: 16px;
                padding: 8px 12px;
                color: {C.get('text')};
                font-size: 12pt;
            }}
            QTextEdit:focus {{
                border: 2px solid {C.get('accent')};
            }}
        """)

    def _emit_send(self) -> None:
        """استخراج متن و ارسال سیگنال."""
        text = self.input.toPlainText().strip()
        if not text:
            return
        if self.on_send:
            self.on_send(text)
        self.send_clicked.emit(text)
        self.input.clear()
        self.input.setFocus()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """ارسال با Enter معمولی (بدون Shift)."""
        if event.key() == Qt.Key.Key_Return and not event.modifiers():
            self._emit_send()
        else:
            super().keyPressEvent(event)

    def set_enabled(self, enabled: bool) -> None:
        self.input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)

    def show_abort_button(self, visible: bool) -> None:
        """نمایش یا مخفی‌سازی دکمه Abort (و برعکس دکمه Send)."""
        self.abort_btn.setVisible(visible)
        self.send_btn.setVisible(not visible)