"""
widgets/chat_area.py — ناحیه‌ی نمایش مکالمه

ویژگی‌ها:
    - هدر با برچسب ارائه‌دهنده، کمبوباکس انتخاب مدل، دکمه‌های جستجو و پاکسازی
    - نوار جستجو برای فیلتر زنده‌ی پیام‌ها
    - حباب‌های پیام با رندر Markdown (کد، جدول، لیست)
    - دکمه‌های کپی و بازتولید برای پیام‌های دستیار
    - قابلیت استریم (ساخت یک حباب موقت و به‌روزرسانی HTML)
    - اکسپورت به Markdown
"""

from __future__ import annotations

import markdown
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTextBrowser, QPushButton,
    QScrollArea, QSizePolicy, QComboBox, QFrame, QLineEdit, QApplication,
    QFileDialog,
)
from theme import C, THEMES


class MessageBubble(QFrame):
    """حباب پیام تکی با پشتیبانی از Markdown و دکمه‌های عملیاتی."""

    copy_clicked = pyqtSignal(str)
    regenerate_clicked = pyqtSignal()
    resend_requested = pyqtSignal(str)  # برای خطاها (ارسال مجدد)

    def __init__(
        self,
        text: str,
        is_user: bool,
        error: bool = False,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.text = text
        self.is_user = is_user
        self.setObjectName("bubble")
        self.setFrameShape(QFrame.Shape.StyledPanel)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        # محتوای پیام
        self.content = QTextBrowser()
        self.content.setOpenExternalLinks(True)
        self.content.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.content.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.content.setMaximumWidth(600)
        self._set_content(text)
        # تنظیم ارتفاع بر اساس محتوا
        self.content.document().setDocumentMargin(4)
        self.content.setFixedHeight(int(self.content.document().size().height()) + 10)
        layout.addWidget(self.content)

        # ردیف دکمه‌ها
        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        if not is_user:
            # دکمه کپی
            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(26, 26)
            copy_btn.setToolTip("کپی متن")
            copy_btn.clicked.connect(lambda: self.copy_clicked.emit(text))
            btn_row.addWidget(copy_btn)

            # دکمه بازتولید
            regen_btn = QPushButton("🔄")
            regen_btn.setFixedSize(26, 26)
            regen_btn.setToolTip("تولید دوباره‌ی پاسخ")
            regen_btn.clicked.connect(self.regenerate_clicked)
            btn_row.addWidget(regen_btn)

            if error:
                retry_btn = QPushButton("🔁 ارسال مجدد")
                retry_btn.setToolTip("تلاش دوباره برای دریافت پاسخ")
                retry_btn.clicked.connect(lambda: self.resend_requested.emit(text))
                btn_row.addWidget(retry_btn)
        else:
            copy_btn = QPushButton("📋")
            copy_btn.setFixedSize(26, 26)
            copy_btn.setToolTip("کپی متن")
            copy_btn.clicked.connect(lambda: self.copy_clicked.emit(text))
            btn_row.addWidget(copy_btn)

        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._apply_style()

    def _set_content(self, text: str) -> None:
        """تبدیل Markdown به HTML و تنظیم محتوا."""
        if self.is_user:
            html = f"<div style='color:{C.get('text')}; white-space: pre-wrap;'>{text}</div>"
        else:
            # افزونه‌های Markdown
            extensions = ['fenced_code', 'tables', 'codehilite']
            try:
                html = markdown.markdown(text, extensions=extensions)
            except Exception:
                html = text
            html = f"<div style='color:{C.get('text')};'>{html}</div>"
        self.content.setHtml(html)

    def update_text(self, new_text: str) -> None:
        """به‌روزرسانی متن حباب و ارتفاع (برای استریم)."""
        self.text = new_text
        self._set_content(new_text)
        self.content.setFixedHeight(int(self.content.document().size().height()) + 10)

    def _apply_style(self) -> None:
        bg = C.get("bubble_user") if self.is_user else C.get("bubble_bot")
        radius = C.get("radius")
        self.setStyleSheet(f"""
            #bubble {{
                background: {bg};
                border-radius: {radius};
                margin: 4px 8px;
            }}
        """)

    def update_theme(self) -> None:
        """به‌روزرسانی استایل با تم جدید."""
        self._apply_style()
        # به‌روزرسانی رنگ متن در HTML
        self._set_content(self.text)


class ChatHeader(QWidget):
    """هدر بالای ناحیه‌ی چت شامل تنظیمات، انتخاب مدل و جستجو."""

    settings_clicked = pyqtSignal()
    clear_clicked = pyqtSignal()
    model_changed = pyqtSignal(str)
    search_toggled = pyqtSignal(bool)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 6, 10, 6)
        layout.setSpacing(8)

        self.provider_label = QLabel("🤗 HuggingFace")
        self.provider_label.setFont(QFont(C.get("font"), 10, QFont.Weight.Bold))
        layout.addWidget(self.provider_label)

        layout.addStretch()

        # دکمه جستجو
        self.search_btn = QPushButton("🔍")
        self.search_btn.setFixedSize(28, 28)
        self.search_btn.setToolTip("جستجو در مکالمه (Ctrl+F)")
        self.search_btn.clicked.connect(self._toggle_search)
        layout.addWidget(self.search_btn)

        # انتخاب مدل
        self.model_combo = QComboBox()
        self.model_combo.setMinimumWidth(180)
        self.model_combo.addItems([
            "Mistral-7B-Instruct (v0.3)", "Gemma-2-2B-it",
            "Qwen2.5-7B-Instruct", "DeepSeek-R1-Distill-Qwen-1.5B",
            "Phi-3-mini-4k-instruct"
        ])
        self.model_combo.currentTextChanged.connect(self.model_changed)
        layout.addWidget(self.model_combo)

        # دکمه پاکسازی
        self.clear_btn = QPushButton("🗑️")
        self.clear_btn.setFixedSize(28, 28)
        self.clear_btn.setToolTip("پاک کردن تاریخچه (Ctrl+N)")
        self.clear_btn.clicked.connect(self.clear_clicked)
        layout.addWidget(self.clear_btn)

        # دکمه تنظیمات
        self.settings_btn = QPushButton("⚙️")
        self.settings_btn.setFixedSize(28, 28)
        self.settings_btn.setToolTip("تنظیمات (Ctrl+,)")
        self.settings_btn.clicked.connect(self.settings_clicked)
        layout.addWidget(self.settings_btn)

        self.typing_label = QLabel("")
        self.typing_label.setFont(QFont(C.get("font"), 9))
        layout.addWidget(self.typing_label)

        self._apply_style()

    def _toggle_search(self) -> None:
        """وضعیت جستجو را معکوس می‌کند."""
        self.search_toggled.emit(True)  # منطق در ChatArea

    def set_typing(self, status: bool) -> None:
        self.typing_label.setText("⚡ در حال تایپ..." if status else "")

    def set_provider_label(self, label: str) -> None:
        self.provider_label.setText(label)

    def _apply_style(self) -> None:
        self.setStyleSheet(f"""
            QWidget {{
                background: {C.get('sidebar')};
                border-radius: 12px;
            }}
        """)

    def update_theme(self) -> None:
        self._apply_style()


class ChatArea(QWidget):
    """ناحیه‌ی کامل چت: هدر + جستجو + تاریخچه با اسکرول."""

    resend_requested = pyqtSignal(str)   # وقتی کاربر روی retry کلیک کند
    regenerate_requested = pyqtSignal()  # وقتی کاربر regenerate را بزند

    def __init__(
        self,
        on_quick_send=None,
        toast_mgr=None,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.on_quick_send = on_quick_send
        self.toast_mgr = toast_mgr
        self.bubbles: list[MessageBubble] = []
        self._stream_bubble: MessageBubble | None = None
        self._typing_indicator: QLabel | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # هدر
        self.header = ChatHeader()
        layout.addWidget(self.header)

        # نوار جستجو
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("جستجو در مکالمه...")
        self.search_bar.setVisible(False)
        self.search_bar.textChanged.connect(self._filter_messages)
        layout.addWidget(self.search_bar)

        # ناحیه اسکرول
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        self.container = QWidget()
        self.msgs_layout = QVBoxLayout(self.container)
        self.msgs_layout.setContentsMargins(4, 4, 4, 4)
        self.msgs_layout.setSpacing(2)
        self.msgs_layout.addStretch()
        self.scroll.setWidget(self.container)
        layout.addWidget(self.scroll)

        # اتصال سیگنال هدر به نوار جستجو
        self.header.search_toggled.connect(self._toggle_search_bar)

    def _toggle_search_bar(self, _=None) -> None:
        """نمایش/مخفی کردن نوار جستجو."""
        self.search_bar.setVisible(not self.search_bar.isVisible())
        if self.search_bar.isVisible():
            self.search_bar.setFocus()

    def _filter_messages(self, text: str) -> None:
        """فیلتر حباب‌ها بر اساس متن جستجو."""
        for bubble in self.bubbles:
            bubble.setVisible(text.lower() in bubble.text.lower())

    # ── افزودن پیام ─────────────────────────────────────
    def add_message(self, text: str, is_user: bool = True, error: bool = False) -> MessageBubble:
        """اضافه کردن یک حباب کامل به انتهای چت."""
        bubble = MessageBubble(text, is_user, error)
        bubble.copy_clicked.connect(self._copy_to_clipboard)
        bubble.regenerate_clicked.connect(self.regenerate_requested)
        bubble.resend_requested.connect(self.resend_requested)
        self._insert_bubble(bubble)
        self.bubbles.append(bubble)
        self._scroll_to_bottom()
        return bubble

    def _insert_bubble(self, bubble: MessageBubble) -> None:
        """قرار دادن حباب قبل از stretch انتهایی."""
        idx = self.msgs_layout.count() - 1  # قبل از stretch
        self.msgs_layout.insertWidget(idx, bubble)

    # ── استریم ─────────────────────────────────────────
    def begin_stream(self) -> MessageBubble:
        """ایجاد یک حباب موقت برای دریافت تکه‌های پاسخ."""
        if self._stream_bubble:
            self.msgs_layout.removeWidget(self._stream_bubble)
            self._stream_bubble.deleteLater()
        self._stream_bubble = MessageBubble("", is_user=False)
        self._insert_bubble(self._stream_bubble)
        return self._stream_bubble

    def append_stream_chunk(self, chunk: str) -> None:
        """به‌روزرسانی متن حباب استریم با قطعه جدید."""
        if self._stream_bubble:
            new_text = self._stream_bubble.text + chunk
            self._stream_bubble.update_text(new_text)
            self._scroll_to_bottom()

    def end_stream(self) -> None:
        """اتمام استریم؛ حباب موقت به لیست اضافه می‌شود."""
        if self._stream_bubble:
            self.bubbles.append(self._stream_bubble)
            self._stream_bubble = None

    def show_typing(self) -> None:
        """نمایش نشانگر تایپ (برای حالت غیر استریم)."""
        if not self._typing_indicator:
            self._typing_indicator = QLabel("⚡ در حال تایپ...")
            self._typing_indicator.setAlignment(Qt.AlignmentFlag.AlignLeft)
            idx = self.msgs_layout.count() - 1
            self.msgs_layout.insertWidget(idx, self._typing_indicator)
        self._typing_indicator.setVisible(True)

    def hide_typing(self) -> None:
        if self._typing_indicator:
            self._typing_indicator.setVisible(False)

    # ── مدیریت تاریخچه ────────────────────────────────
    def load_history(self, history: list[dict]) -> None:
        """بارگذاری تاریخچه از لیست پیام‌ها."""
        for msg in history:
            self.add_message(
                msg["content"],
                is_user=(msg["role"] == "user"),
            )

    def clear_messages(self) -> None:
        """حذف تمام حباب‌ها."""
        for b in self.bubbles:
            self.msgs_layout.removeWidget(b)
            b.deleteLater()
        self.bubbles.clear()
        if self._stream_bubble:
            self.msgs_layout.removeWidget(self._stream_bubble)
            self._stream_bubble.deleteLater()
            self._stream_bubble = None

    def remove_last_assistant_bubble(self) -> None:
        """حذف آخرین حباب دستیار (برای regenerate)."""
        # یافتن آخرین حباب دستیار در لیست
        for b in reversed(self.bubbles):
            if not b.is_user:
                self.bubbles.remove(b)
                self.msgs_layout.removeWidget(b)
                b.deleteLater()
                break

    def restore_welcome(self) -> None:
        """بازگرداندن حالت خوش‌آمدگویی (در صورت نیاز)."""
        # در این نسخه فقط پاکسازی می‌کنیم
        self.clear_messages()

    def dismiss_welcome(self) -> None:
        pass  # چیزی برای مخفی کردن نداریم

    # ── عملیات جانبی ──────────────────────────────────
    def export_chat(self) -> None:
        """خروجی گرفتن از مکالمه در فرمت Markdown."""
        path, _ = QFileDialog.getSaveFileName(
            self, "ذخیره مکالمه", "chat_export.md", "Markdown (*.md)"
        )
        if not path:
            return
        try:
            with open(path, "w", encoding="utf-8") as f:
                for b in self.bubbles:
                    role = "**شما**" if b.is_user else "**دستیار**"
                    f.write(f"{role}:\n{b.text}\n\n")
            if self.toast_mgr:
                self.toast_mgr.show("✓ گفتگو با موفقیت ذخیره شد", "success")
        except Exception as e:
            if self.toast_mgr:
                self.toast_mgr.show(f"خطا در ذخیره‌سازی: {e}", "error")

    def _copy_to_clipboard(self, text: str) -> None:
        """کپی متن در کلیپ‌بورد و نمایش اعلان."""
        QApplication.clipboard().setText(text)
        if self.toast_mgr:
            self.toast_mgr.show("✅ متن کپی شد", "success")

    def _scroll_to_bottom(self) -> None:
        """اسکرول نرم به انتهای چت."""
        QTimer.singleShot(20, lambda: self.scroll.verticalScrollBar().setValue(
            self.scroll.verticalScrollBar().maximum()
        ))

    def update_theme(self) -> None:
        """به‌روزرسانی استایل تمام حباب‌ها و هدر با تم جدید."""
        self.header.update_theme()
        for b in self.bubbles:
            b.update_theme()
        if self._stream_bubble:
            self._stream_bubble.update_theme()