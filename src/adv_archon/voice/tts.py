"""Text-to-Speech — requiere: pip install adv-archon[voice] (pyttsx3)."""


class TTSClient:
    """Síntesis de voz local con pyttsx3. Instala con: pip install pyttsx3"""

    def __init__(self, rate: int = 175, volume: float = 0.9):
        self.rate = rate
        self.volume = volume
        self._engine = None

    def _load(self):
        if self._engine is not None:
            return
        try:
            import pyttsx3
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.rate)
            self._engine.setProperty("volume", self.volume)
        except ImportError:
            raise RuntimeError(
                "pyttsx3 no está instalado. Ejecuta: pip install pyttsx3"
            )

    def speak(self, text: str):
        self._load()
        self._engine.say(text)
        self._engine.runAndWait()

    def speak_async(self, text: str):
        import threading
        threading.Thread(target=self.speak, args=(text,), daemon=True).start()
