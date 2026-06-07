"""
widgets/settings_dialog.py — دیالوگ تنظیمات پیشرفته

ویژگی‌ها:
    - سه تب: مدل و API، پارامترهای تولید، ظاهر
    - ورود توکن Hugging Face، انتخاب مدل، دما، حداکثر توکن، system prompt
    - انتخاب تم از بین ۴ تم از پیش تعریف‌شده
    - ذخیره‌سازی بلادرنگ و انتشار سیگنال تنظیمات جدید
"""

from __future__ import annotations

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QFormLayout,
    QLineEdit, QComboBox, QDoubleSpinBox, QSpinBox, QPushButton,
    QHBoxLayout, QMessageBox,
)
from config import Config, PROVIDER_LABELS, HF_MODELS
from theme import THEMES


class SettingsDialog(QDialog):
    """دیالوگ مودال برای ویرایش تمام تنظیمات برنامه."""

    settings_saved = pyqtSignal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("تنظیمات Nexus AI")
        self.setMinimumWidth(450)

        layout = QVBoxLayout(self)
        tabs = QTabWidget()
        layout.addWidget(tabs)

        # ── تب ۱: مدل و API ───────────────────────────
        model_tab = QWidget()
        form_model = QFormLayout(model_tab)

        self.provider_combo = QComboBox()
        self.provider_combo.addItems(PROVIDER_LABELS.keys())
        self.provider_combo.setCurrentText(Config.get("api_provider", "huggingface"))
        form_model.addRow("ارائه‌دهنده:", self.provider_combo)

        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.token_input.setText(Config.get("hf_token", ""))
        self.token_input.setPlaceholderText("hf_xxxxxxxxxxxxxxxxxxxxxxxxxx")
        form_model.addRow("توکن HuggingFace:", self.token_input)

        self.model_combo = QComboBox()
        self.model_combo.addItems(HF_MODELS.keys())
        current_model = Config.get("hf_model")
        if current_model in HF_MODELS:
            self.model_combo.setCurrentText(current_model)
        form_model.addRow("مدل:", self.model_combo)

        tabs.addTab(model_tab, "مدل و API")

        # ── تب ۲: پارامترهای تولید ───────────────────
        param_tab = QWidget()
        form_param = QFormLayout(param_tab)

        self.temp_spin = QDoubleSpinBox()
        self.temp_spin.setRange(0.0, 2.0)
        self.temp_spin.setSingleStep(0.05)
        self.temp_spin.setDecimals(2)
        self.temp_spin.setValue(Config.get("temperature", 0.7))
        form_param.addRow("دما (Temperature):", self.temp_spin)

        self.max_tokens_spin = QSpinBox()
        self.max_tokens_spin.setRange(64, 8192)
        self.max_tokens_spin.setSingleStep(64)
        self.max_tokens_spin.setValue(Config.get("max_tokens", 2048))
        form_param.addRow("حداکثر توکن:", self.max_tokens_spin)

        self.system_prompt_input = QLineEdit()
        self.system_prompt_input.setText(Config.get("system_prompt", ""))
        form_param.addRow("System Prompt:", self.system_prompt_input)

        tabs.addTab(param_tab, "پارامترها")

        # ── تب ۳: ظاهر ──────────────────────────────
        appear_tab = QWidget()
        form_appear = QFormLayout(appear_tab)

        self.theme_combo = QComboBox()
        self.theme_combo.addItems(THEMES.keys())
        current_theme = Config.get("theme", "dark_glass")
        if current_theme in THEMES:
            self.theme_combo.setCurrentText(current_theme)
        form_appear.addRow("تم:", self.theme_combo)

        self.stream_combo = QComboBox()
        self.stream_combo.addItems(["فعال", "غیرفعال"])
        self.stream_combo.setCurrentText("فعال" if Config.get("streaming", True) else "غیرفعال")
        form_appear.addRow("استریم:", self.stream_combo)

        tabs.addTab(appear_tab, "ظاهر")

        # ── دکمه‌های پایین ──────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        save_btn = QPushButton("💾 ذخیره تنظیمات")
        save_btn.setDefault(True)
        save_btn.clicked.connect(self._save)
        btn_row.addWidget(save_btn)

        cancel_btn = QPushButton("انصراف")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        layout.addLayout(btn_row)

    def _save(self) -> None:
        """اعتبارسنجی و ذخیره‌سازی تمام مقادیر."""
        token = self.token_input.text().strip()
        if not token and self.provider_combo.currentText() == "huggingface":
            QMessageBox.warning(
                self,
                "توکن الزامی",
                "برای استفاده از مدل‌های Hugging Face باید توکن API را وارد کنید."
            )
            return

        Config.set("api_provider", self.provider_combo.currentText())
        Config.set("hf_token", token)
        Config.set("hf_model", self.model_combo.currentText())
        Config.set("temperature", self.temp_spin.value())
        Config.set("max_tokens", self.max_tokens_spin.value())
        Config.set("system_prompt", self.system_prompt_input.text())
        Config.set("theme", self.theme_combo.currentText())
        Config.set("streaming", self.stream_combo.currentText() == "فعال")

        self.settings_saved.emit()
        self.accept()