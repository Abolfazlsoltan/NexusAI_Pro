"""
main_qt.py — NexusAI v6 Titan (نسخه نهایی ضدکراش با Splash + نصب خودکار وابستگی‌ها)

✅ راه‌اندازی مجدد برنامه پس از نصب خودکار کتابخانه‌های اصلی
✅ نمایش Splash Screen پیشرفته با نوار پیشرفت
✅ مدیریت خطای سراسری بدون بسته شدن ناگهانی
✅ Import ایمن با Fallback برای کتابخانه‌های اختیاری (markdown)
✅ اجرای بدون نقص حتی در محیط‌های ناقص
✅ رفع مشکل صفحهٔ سیاه ناشی از عدم نصب markdown با تزریق ماژول مجازی
✅ تایم‌اوت ۵ ثانیه‌ای برای نصب markdown جهت جلوگیری از قفل شدن Splash
"""

import sys
import subprocess
import traceback
import os
import types
from pathlib import Path

# ── 0. نصب خودکار و راه‌اندازی مجدد (قبل از هر import سنگین) ──────
def _bootstrap_dependencies():
    """
    کتابخانه‌های اصلی را بررسی می‌کند و در صورت نبود نصب می‌کند.
    بعد از نصب، برنامه را مجدداً اجرا می‌کند تا importها تازه شوند.
    """
    essential = ["PyQt6", "huggingface_hub"]
    missing = []
    for lib in essential:
        try:
            __import__(lib)
        except ImportError:
            missing.append(lib)

    if not missing:
        return

    print(f"📦 در حال نصب کتابخانه‌های ضروری: {', '.join(missing)}")
    try:
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-q"] + missing,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
        print("🔄 راه‌اندازی مجدد برنامه...")
        os.execv(sys.executable, [sys.executable] + sys.argv)
    except Exception as e:
        print(f"❌ نصب خودکار ناموفق بود: {e}")
        sys.exit(1)

_bootstrap_dependencies()

# ── 1. ایمپورت markdown با fallback و تزریق ماژول مجازی ─────────
MARKDOWN_AVAILABLE = False
try:
    import markdown as md_lib
    MARKDOWN_AVAILABLE = True
except ImportError:
    # کلاس fallback ساده
    class DummyMarkdown:
        @staticmethod
        def markdown(text, *args, **kwargs):
            return f"<pre>{text}</pre>"

    md_lib = DummyMarkdown()
    # ساخت یک ماژول مجازی و ثبت در sys.modules
    # تا هر ایمپورت بعدی از markdown (مثلاً در ChatArea) با خطا مواجه نشود
    dummy_module = types.ModuleType("markdown")
    dummy_module.markdown = DummyMarkdown.markdown
    # در صورت نیاز می‌توان توابع یا کلاس‌های دیگری هم اضافه کرد
    sys.modules["markdown"] = dummy_module

# ── 2. hook سراسری برای خطاهای ناشناخته ─────────────────────────
_original_excepthook = sys.excepthook

def _global_exception_hook(exc_type, exc_value, exc_tb):
    traceback.print_exception(exc_type, exc_value, exc_tb)
    try:
        from PyQt6.QtWidgets import QApplication, QMessageBox
        if QApplication.instance():
            QMessageBox.critical(None, "خطای بحرانی",
                                 f"یک خطای پیش‌بینی‌نشده رخ داد:\n\n{exc_value}")
    except Exception:
        pass
    _original_excepthook(exc_type, exc_value, exc_tb)

sys.excepthook = _global_exception_hook

# ── 3. importهای ایمن با Fallback ─────────────────────────────
IMPORTS_OK = True
missing_libs = []

try:
    from PyQt6.QtCore import Qt, QSize, QTimer, QSettings
    from PyQt6.QtGui import QFont, QKeySequence, QShortcut
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QMessageBox, QWidget, QVBoxLayout,
        QLabel, QDialog, QProgressBar
    )
except ImportError as e:
    IMPORTS_OK = False
    missing_libs.append("PyQt6")

# ماژول‌های داخلی
try:
    from config import Config, History, PROVIDER_LABELS, HF_MODELS
except ImportError:
    Config = type('Config', (), {'load': lambda: None, 'get': lambda k, d=None: d, 'set': lambda k, v: None})()
    History = type('History', (), {'load': lambda: [], 'save': lambda h: None, 'clear': lambda: None})()
    PROVIDER_LABELS = {}
    HF_MODELS = {"default": "mistralai/Mistral-7B-Instruct-v0.1"}

try:
    from fonts_qt import load_vazir
except ImportError:
    load_vazir = lambda: False

try:
    from api_client import HuggingFaceWorker
except ImportError:
    HuggingFaceWorker = None

try:
    from theme import C, apply_global_style
except ImportError:
    C = type('C', (), {'current_theme': 'dark_glass', 'set_theme': lambda t: None, 'add_listener': lambda f: None})()
    apply_global_style = lambda: ""

# Widgets – به لطف تزریق markdown، ایمپورت ChatArea موفق خواهد بود
ChatArea = InputBar = SettingsDialog = ToastManager = None
try:
    from widgets.chat_area import ChatArea
except ImportError:
    pass
try:
    from widgets.input_bar import InputBar
except ImportError:
    pass
try:
    from widgets.settings_dialog import SettingsDialog
except ImportError:
    pass
try:
    from widgets.toast import ToastManager
except ImportError:
    pass

BASE_WIDTH, BASE_HEIGHT = 480, 900


# ── 4. Splash Screen حرفه‌ای ─────────────────────────────────
def show_splash():
    """یک QDialog بی‌حاشیه به‌عنوان Splash نمایش می‌دهد"""
    try:
        splash = QDialog()
        splash.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        splash.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        splash.setFixedSize(400, 200)

        layout = QVBoxLayout(splash)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("Nexus AI v6 Titan")
        title.setStyleSheet("color: white; font-size: 20pt; font-weight: bold;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        splash.status_label = QLabel("در حال راه‌اندازی...")
        splash.status_label.setStyleSheet("color: #cccccc; font-size: 12pt;")
        splash.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(splash.status_label)

        splash.progress = QProgressBar()
        splash.progress.setRange(0, 100)
        splash.progress.setValue(30)
        splash.progress.setStyleSheet("""
            QProgressBar {
                border: 1px solid #5E81AC;
                border-radius: 10px;
                background: rgba(30, 30, 40, 0.8);
                height: 10px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: #5E81AC;
                border-radius: 10px;
            }
        """)
        layout.addWidget(splash.progress)

        splash.setStyleSheet("background: rgba(20, 20, 30, 0.9); border-radius: 20px;")
        return splash
    except Exception:
        return None


# ── 5. پنجره اصلی ───────────────────────────────────────────
class NexusWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        if not IMPORTS_OK:
            self._show_fatal_error(
                "کتابخانه‌های ضروری نصب نیستند:\n" +
                "\n".join(f"• {lib}" for lib in missing_libs) +
                "\n\nلطفاً برنامه را دوباره اجرا کنید."
            )
            return

        # بارگذاری تنظیمات
        Config.load()

        # تم
        try:
            C.set_theme(Config.get("theme", "dark_glass"))
        except Exception:
            pass

        self.setWindowTitle("Nexus AI v6 Titan")
        self.setObjectName("NexusWindow")
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setStyleSheet(apply_global_style())
        self.setMinimumSize(QSize(380, 600))

        self._busy = False
        self._first_message = True
        self._api_worker = None
        self._history = []
        self._streaming_active = False
        self._last_user_text = ""
        self._ai_bubble = None
        self.toast_mgr = ToastManager(self) if ToastManager else None

        self._build_ui()
        self._setup_shortcuts()
        self._resize_initial()
        self._update_header_status()

        C.add_listener(self._on_theme_change)

        try:
            saved = History.load()
            if saved:
                self._history = saved
                if self.chat:
                    self.chat.load_history(saved)
                self._first_message = False
        except Exception:
            pass

    def _show_fatal_error(self, msg):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        lbl = QLabel(msg)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl)

    def _on_theme_change(self, _):
        self.setStyleSheet(apply_global_style())
        if self.chat:
            self.chat.update_theme()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.chat = ChatArea(on_quick_send=self._user_send, toast_mgr=self.toast_mgr) if ChatArea else None
        if self.chat:
            layout.addWidget(self.chat)

        self.bar = InputBar(on_send=self._user_send, toast_mgr=self.toast_mgr) if InputBar else None
        if self.bar:
            layout.addWidget(self.bar)

        if self.chat and self.chat.header:
            self.chat.header.settings_clicked.connect(self._open_settings)
            self.chat.header.clear_clicked.connect(self._clear_chat)
            self.chat.header.model_changed.connect(self._on_model_changed)
        if self.chat:
            self.chat.resend_requested.connect(self._resend_last_user)
            try:
                self.chat.regenerate_requested.connect(self._regenerate_last)
            except AttributeError:
                pass
        if self.bar:
            self.bar.abort_requested.connect(self._abort_streaming)

    def _setup_shortcuts(self):
        try:
            QShortcut(QKeySequence("Ctrl+,"), self).activated.connect(self._open_settings)
            QShortcut(QKeySequence("Ctrl+N"), self).activated.connect(self._clear_chat)
            QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(self._toggle_search)
            if self.chat:
                QShortcut(QKeySequence("Ctrl+E"), self).activated.connect(self.chat.export_chat)
            QShortcut(QKeySequence("Escape"), self).activated.connect(self._on_escape)
        except Exception:
            pass

    def _resize_initial(self):
        try:
            screen = QApplication.primaryScreen()
            if screen and screen.availableGeometry().width() > 500:
                self.resize(BASE_WIDTH, BASE_HEIGHT)
        except Exception:
            self.resize(BASE_WIDTH, BASE_HEIGHT)

    def _update_header_status(self):
        try:
            provider = Config.get("api_provider", "huggingface")
            label = PROVIDER_LABELS.get(provider, provider)
            model = Config.get("hf_model", "")
            if self.chat and self.chat.header:
                self.chat.header.set_provider_label(f"{label}  |  {model}" if model else label)
        except Exception:
            pass

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.toast_mgr:
            try:
                self.toast_mgr.update_position()
            except Exception:
                pass

    def _toggle_search(self):
        if self.chat and hasattr(self.chat, 'search_bar'):
            try:
                self.chat.search_bar.setVisible(not self.chat.search_bar.isVisible())
                if self.chat.search_bar.isVisible():
                    self.chat.search_bar.setFocus()
            except Exception:
                pass

    def _on_model_changed(self, model_name):
        Config.set("hf_model", model_name)
        self._update_header_status()
        if self.toast_mgr:
            self.toast_mgr.show(f"مدل به {model_name} تغییر یافت", "info")

    def _on_escape(self):
        if self._streaming_active or self._busy:
            self._abort_streaming()

    def _user_send(self, text):
        text = text.strip()
        if not text or self._busy:
            return
        self._busy = True
        self._last_user_text = text
        if self.bar:
            self.bar.set_enabled(False)
        if self._first_message and self.chat:
            self.chat.dismiss_welcome()
            self._first_message = False
        if self.chat:
            try:
                self.chat.add_message(text, is_user=True)
            except Exception as e:
                self._on_api_error(f"خطا در نمایش پیام: {e}")
                return
        self._history.append({"role": "user", "content": text})
        QTimer.singleShot(100, self._ai_start)

    def _resend_last_user(self, _=None):
        if self._last_user_text:
            self._user_send(self._last_user_text)

    def _regenerate_last(self):
        if self._busy or not self._history:
            return
        try:
            if self._history and self._history[-1]["role"] == "assistant":
                self._history.pop()
            if self.chat:
                self.chat.remove_last_assistant_bubble()
        except Exception:
            pass
        if self._last_user_text:
            self._user_send(self._last_user_text)

    def _ai_start(self):
        if not HuggingFaceWorker:
            self._on_api_error("ماژول ارتباط با API یافت نشد.")
            return
        try:
            provider = Config.get("api_provider", "huggingface")
            if provider != "huggingface":
                self._on_api_error("فعلاً فقط مدل‌های Hugging Face پشتیبانی می‌شوند.")
                return
            token = Config.get("hf_token", "")
            if not token:
                self._on_api_error("توکن Hugging Face تنظیم نشده. از تنظیمات وارد کنید.")
                return
            model_name = Config.get("hf_model", list(HF_MODELS.keys())[0])
            model_id = HF_MODELS.get(model_name)
            if not model_id:
                self._on_api_error(f"مدل '{model_name}' یافت نشد.")
                return
            streaming = Config.get("streaming", True)
            self._api_worker = HuggingFaceWorker(
                messages=list(self._history),
                model_id=model_id,
                token=token,
                max_tokens=Config.get("max_tokens", 2048),
                temperature=Config.get("temperature", 0.7),
            )
            self._api_worker.stream_started.connect(self._on_stream_started)
            self._api_worker.chunk_received.connect(self._on_chunk)
            self._api_worker.response_ready.connect(self._on_ai_response)
            self._api_worker.error_occurred.connect(self._on_api_error)
            self._api_worker.aborted.connect(self._on_aborted)
            self._api_worker.token_count.connect(self._on_token_count)
            self._api_worker.start()
            if streaming:
                self._streaming_active = True
                self._ai_bubble = self.chat.begin_stream() if self.chat else None
                if self.bar:
                    self.bar.show_abort_button(True)
            else:
                self._streaming_active = False
                if self.chat:
                    self.chat.show_typing()
        except Exception as e:
            self._on_api_error(f"خطا در شروع درخواست: {e}")

    def _on_stream_started(self):
        if self.chat and self.chat.header:
            self.chat.header.set_typing(True)

    def _on_chunk(self, chunk):
        if self._streaming_active and self.chat:
            self.chat.append_stream_chunk(chunk)

    def _on_ai_response(self, text):
        try:
            if self.bar:
                self.bar.show_abort_button(False)
            if self._streaming_active:
                if self.chat:
                    self.chat.end_stream()
                    if self.chat.header:
                        self.chat.header.set_typing(False)
                self._streaming_active = False
            else:
                if self.chat:
                    self.chat.hide_typing()
                    self.chat.add_message(text, is_user=False)
            if text.strip():
                self._history.append({"role": "assistant", "content": text})
                History.save(self._history)
        except Exception as e:
            self._on_api_error(f"خطا در دریافت پاسخ: {e}")
        finally:
            self._busy = False
            if self.bar:
                self.bar.set_enabled(True)

    def _on_api_error(self, error_msg):
        try:
            if self.bar:
                self.bar.show_abort_button(False)
            if self._streaming_active:
                if self.chat:
                    self.chat.end_stream()
                    if self.chat.header:
                        self.chat.header.set_typing(False)
                self._streaming_active = False
            else:
                if self.chat:
                    self.chat.hide_typing()
            if self.chat:
                self.chat.add_message(f"⚠️ {error_msg}", is_user=False, error=True)
            if self.toast_mgr:
                self.toast_mgr.show(f"خطا: {error_msg}", "error", 4000)
        except Exception:
            pass
        finally:
            self._busy = False
            if self.bar:
                self.bar.set_enabled(True)

    def _on_aborted(self):
        try:
            if self.bar:
                self.bar.show_abort_button(False)
            if self.chat and self.chat.header:
                self.chat.header.set_typing(False)
            if self._streaming_active:
                if self.chat:
                    self.chat.end_stream()
                self._streaming_active = False
            else:
                if self.chat:
                    self.chat.hide_typing()
        except Exception:
            pass
        finally:
            self._busy = False
            if self.bar:
                self.bar.set_enabled(True)

    def _abort_streaming(self):
        if self._api_worker and self._api_worker.isRunning():
            try:
                self._api_worker.abort()
                if self.toast_mgr:
                    self.toast_mgr.show("⏹ پاسخ متوقف شد", "info")
            except Exception:
                pass

    def _on_token_count(self, count):
        if self.toast_mgr:
            self.toast_mgr.show(f"🧮 مصرف تقریبی توکن: {count}", "info")

    def _open_settings(self):
        if SettingsDialog is None:
            if self.toast_mgr:
                self.toast_mgr.show("تنظیمات در دسترس نیست", "error")
            return
        try:
            dlg = SettingsDialog(self)
            dlg.settings_saved.connect(self._on_settings_saved)
            dlg.exec()
        except Exception as e:
            if self.toast_mgr:
                self.toast_mgr.show(f"خطا در باز کردن تنظیمات: {e}", "error")

    def _on_settings_saved(self):
        try:
            new_theme = Config.get("theme")
            if new_theme != C.current_theme:
                C.set_theme(new_theme)
            self._update_header_status()
            if self.toast_mgr:
                self.toast_mgr.show("✓ تنظیمات با موفقیت ذخیره شد", "success")
        except Exception:
            pass

    def _clear_chat(self):
        if self._busy:
            if self.toast_mgr:
                self.toast_mgr.show("لطفاً تا پایان پاسخ صبر کنید", "error")
            return
        reply = QMessageBox.question(
            self, "پاک‌سازی مکالمه", "همهٔ پیام‌ها حذف شوند؟",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            if self.chat:
                self.chat.clear_messages()
                self.chat.restore_welcome()
            self._history.clear()
            self._first_message = True
            self._last_user_text = ""
            History.clear()
            if self.toast_mgr:
                self.toast_mgr.show("✓ مکالمه پاک شد", "success")


# ── 6. ورود اصلی برنامه ────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Nexus AI v6 Titan")
    app.setApplicationVersion("6.0.0")

    # Splash با نصب کتابخانه‌های اختیاری
    splash = show_splash()
    if splash:
        splash.show()
        splash.progress.setValue(50)
        QApplication.processEvents()
        splash.status_label.setText("بررسی کتابخانه‌های اختیاری...")

        # اگر markdown از قبل نصب نباشد، تلاش برای نصب با تایم‌اوت ۵ ثانیه
        if not MARKDOWN_AVAILABLE:
            try:
                splash.status_label.setText("نصب markdown (حداکثر ۵ ثانیه)...")
                QApplication.processEvents()
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-q", "markdown"],
                    timeout=5,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                # در صورت موفقیت، اجرای فعلی همچنان از ماژول مجازی استفاده می‌کند
                # اما اجرای بعدی کتابخانهٔ واقعی را بارگذاری خواهد کرد
            except (subprocess.TimeoutExpired, Exception):
                # تایم‌اوت یا هر خطای دیگر – برنامه بدون markdown ادامه می‌دهد
                pass

        splash.progress.setValue(80)
        splash.status_label.setText("در حال بارگذاری رابط کاربری...")
        QApplication.processEvents()

    # تنظیم فونت
    try:
        font = QFont()
        font.setFamilies(["Vazir", "IRANSans", "Tahoma", "Segoe UI"])
        font.setPointSize(Config.get("font_size", 12) if Config and hasattr(Config, 'get') else 12)
        app.setFont(font)
    except Exception:
        pass
    load_vazir()

    # ساخت و نمایش پنجره اصلی
    try:
        win = NexusWindow()
        win.show()
        if splash:
            splash.progress.setValue(100)
            splash.status_label.setText("آماده!")
            QTimer.singleShot(800, splash.close)
    except Exception as e:
        if splash:
            splash.close()
        QMessageBox.critical(None, "خطا", f"برنامه نتوانست شروع شود:\n{e}")
        sys.exit(1)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()