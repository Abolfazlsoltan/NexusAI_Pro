"""
api_client.py — کلاینت Hugging Face با استریم واقعی و قابلیت Abort

ویژگی‌ها:
    - اجرا در ترد جداگانه (QThread)
    - استریم تکه‌تکه (chunk-by-chunk) با سیگنال‌های PyQt
    - امکان توقف ناگهانی درخواست
    - تخمین مصرف توکن
"""

from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal
from huggingface_hub import InferenceClient


class HuggingFaceWorker(QThread):
    """کارگری که ارتباط با Hugging Face Inference API را در بک‌گراند مدیریت می‌کند."""

    # سیگنال‌ها
    stream_started = pyqtSignal()
    chunk_received = pyqtSignal(str)
    response_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    aborted = pyqtSignal()
    token_count = pyqtSignal(int)  # تعداد تقریبی توکن مصرفی

    def __init__(
        self,
        messages: list[dict[str, str]],
        model_id: str,
        token: str,
        max_tokens: int = 2048,
        temperature: float = 0.7,
        parent=None,
    ) -> None:
        super().__init__(parent)
        self.messages = messages
        self.model_id = model_id
        self.token = token
        self.max_tokens = max_tokens
        self.temperature = temperature
        self._abort_flag = False

    def run(self) -> None:
        """نقطه‌ی ورود ترد؛ اجرای درخواست استریم."""
        try:
            client = InferenceClient(model=self.model_id, token=self.token)
            self.stream_started.emit()

            stream = client.chat_completion(
                messages=self.messages,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                stream=True,
            )

            full_text = ""
            token_estimate = 0

            for chunk in stream:
                if self._abort_flag:
                    break
                if chunk.choices and chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_text += content
                    self.chunk_received.emit(content)
                    # تخمین خام توکن: حدود هر ۴ کاراکتر یک توکن
                    token_estimate += max(1, len(content) // 4)

            if self._abort_flag:
                self.aborted.emit()
            else:
                self.response_ready.emit(full_text)
                self.token_count.emit(token_estimate)

        except Exception as exc:
            self.error_occurred.emit(str(exc))

    def abort(self) -> None:
        """تنظیم پرچم توقف؛ ترد در گردش بعدی متوقف می‌شود."""
        self._abort_flag = True