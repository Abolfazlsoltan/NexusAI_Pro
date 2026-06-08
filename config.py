"""
config.py — مدیریت پیکربندی، تاریخچه و مدل‌های Hugging Face

ویژگی‌ها:
    - بارگذاری/ذخیره‌سازی تنظیمات در فایل JSON
    - خواندن متغیرهای حساس از فایل .env با استفاده از python-dotenv
    - پشتیبانی از شنونده‌ها برای تغییرات زنده
    - لیست مدل‌های قابل انتخاب با شناسه‌ی Hugging Face
    - مدیریت تاریخچه‌ی مکالمات
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Callable

from dotenv import load_dotenv

# ── بارگذاری متغیرهای محیطی از فایل .env ──────────────
# این خط فایل .env را در دایرکتوری ریشه پروژه جستجو می‌کند
load_dotenv()

# مسیرهای ذخیره‌سازی
APP_NAME = "NexusAI"
CONFIG_DIR = Path.home() / f".{APP_NAME}"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

# ── متغیرهای حساس (API Keys) از محیط ──────────────────
# اگر در .env تعریف نشده باشند، مقادیر پیش‌فرض (خالی) استفاده می‌شوند
HF_TOKEN = os.getenv("HF_TOKEN", "")
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# برچسب ارائه‌دهندگان
PROVIDER_LABELS: dict[str, str] = {
    "huggingface": "🤗 HuggingFace",
    "groq": "⚡ Groq",
    "openai": "🧠 OpenAI",
}

# مدل‌های پیش‌فرض Hugging Face
HF_MODELS: dict[str, str] = {
    "Mistral-7B-Instruct (v0.3)": "mistralai/Mistral-7B-Instruct-v0.3",
    "Gemma-2-2B-it": "google/gemma-2-2b-it",
    "Qwen2.5-7B-Instruct": "Qwen/Qwen2.5-7B-Instruct",
    "DeepSeek-R1-Distill-Qwen-1.5B": "deepseek-ai/DeepSeek-R1-Distill-Qwen-1.5B",
    "Phi-3-mini-4k-instruct": "microsoft/Phi-3-mini-4k-instruct",
}

# پیکربندی پیش‌فرض
DEFAULT_CONFIG: dict[str, Any] = {
    "api_provider": "huggingface",
    "hf_token": HF_TOKEN,  # از متغیر محیطی خوانده می‌شود
    "hf_model": "Mistral-7B-Instruct (v0.3)",
    "groq_api_key": GROQ_API_KEY,  # از متغیر محیطی خوانده می‌شود
    "openai_api_key": OPENAI_API_KEY,  # از متغیر محیطی خوانده می‌شود
    "temperature": 0.7,
    "max_tokens": 2048,
    "system_prompt": "You are a helpful, respectful and honest AI assistant.",
    "theme": "dark_glass",
    "streaming": True,
    "font_size": 12,
}


class Config:
    """مدیریت یکپارچه‌ی تنظیمات برنامه با ذخیره‌سازی خودکار و پشتیبانی از متغیرهای محیطی."""

    _data: dict[str, Any] = {}
    _listeners: list[Callable[[str, Any], None]] = []

    # ── بارگذاری و ذخیره‌سازی ──────────────────────────────
    @classmethod
    def load(cls) -> None:
        """بارگذاری تنظیمات از دیسک، در صورت نبودن ساخته می‌شود.
        
        متغیرهای حساس (API keys) از متغیرهای محیطی (.env) خوانده می‌شوند
        و بر مقادیر ذخیره‌شده در فایل JSON اولویت دارند.
        """
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        if CONFIG_FILE.exists():
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cls._data = json.load(f)
            except (json.JSONDecodeError, OSError):
                cls._data = {}
        else:
            cls._data = {}

        # ترکیب با پیش‌فرض‌ها برای کلیدهای گمشده
        for key, value in DEFAULT_CONFIG.items():
            if key not in cls._data:
                cls._data[key] = value

        # به‌روزرسانی متغیرهای حساس از متغیرهای محیطی
        # (متغیرهای محیطی اولویت دارند)
        cls._data["hf_token"] = HF_TOKEN or cls._data.get("hf_token", "")
        cls._data["groq_api_key"] = GROQ_API_KEY or cls._data.get("groq_api_key", "")
        cls._data["openai_api_key"] = OPENAI_API_KEY or cls._data.get("openai_api_key", "")

    @classmethod
    def save(cls) -> None:
        """ذخیره‌سازی تنظیمات روی دیسک.
        
        ⚠️  هشدار: API keys حساس را در فایل config.json ذخیره نکنید.
        آنها را تنها در فایل .env قرار دهید که در .gitignore نادیده گرفته می‌شود.
        """
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        # فقط تنظیمات غیر حساس را ذخیره کنید
        safe_data = {
            k: v for k, v in cls._data.items()
            if k not in ["hf_token", "groq_api_key", "openai_api_key"]
        }
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(safe_data, f, indent=2, ensure_ascii=False)

    # ── دسترسی به مقادیر ─────────────────────────────────
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """خواندن یک مقدار پیکربندی."""
        return cls._data.get(key, default)

    @classmethod
    def set(cls, key: str, value: Any) -> None:
        """تنظیم یک مقدار و ذخیره‌سازی بلافاصله.
        
        ⚠️  هشدار: متغیرهای حساس (API keys) را از طریق این متد تنظیم نکنید.
        آنها را تنها در فایل .env قرار دهید.
        
        همچنین تمام شنونده‌های ثبت‌شده را خبر می‌کند.
        """
        cls._data[key] = value
        cls.save()
        for callback in cls._listeners:
            try:
                callback(key, value)
            except Exception:
                pass

    # ── سیستم شنونده‌ها (Live Update) ──────────────────
    @classmethod
    def add_listener(cls, callback: Callable[[str, Any], None]) -> None:
        """افزودن یک شنونده برای تغییرات تنظیمات."""
        if callback not in cls._listeners:
            cls._listeners.append(callback)

    @classmethod
    def remove_listener(cls, callback: Callable[[str, Any], None]) -> None:
        """حذف شنونده."""
        if callback in cls._listeners:
            cls._listeners.remove(callback)


class History:
    """مدیریت تاریخچه‌ی مکالمه (لیست پیام‌های نقش‌دار)."""

    @staticmethod
    def load() -> list[dict[str, str]]:
        """بارگذاری تاریخچه از فایل JSON."""
        if HISTORY_FILE.exists():
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, OSError):
                return []
        return []

    @staticmethod
    def save(messages: list[dict[str, str]]) -> None:
        """ذخیره‌ی تاریخچه روی دیسک."""
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(messages, f, indent=2, ensure_ascii=False)

    @staticmethod
    def clear() -> None:
        """حذف فایل تاریخچه."""
        if HISTORY_FILE.exists():
            HISTORY_FILE.unlink(missing_ok=True)
