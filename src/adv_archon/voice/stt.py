"""Speech-to-Text — requiere: pip install adv-archon[voice] (faster-whisper)."""
from pathlib import Path


class STTClient:
    """Transcripción local con faster-whisper. Instala con: pip install faster-whisper"""

    def __init__(self, model_size: str = "base"):
        self.model_size = model_size
        self._model = None

    def _load(self):
        if self._model is not None:
            return
        try:
            from faster_whisper import WhisperModel
            self._model = WhisperModel(self.model_size, device="cpu", compute_type="int8")
        except ImportError:
            raise RuntimeError(
                "faster-whisper no está instalado. Ejecuta: pip install faster-whisper"
            )

    def transcribe(self, audio_path: str) -> str:
        self._load()
        segments, _ = self._model.transcribe(audio_path)
        return " ".join(s.text.strip() for s in segments)
