"""Fachada LLM — delega en OllamaClient como único motor."""
from adv_archon.integrations.ollama import OllamaClient


class LLMClient:
    """Wrapper fino sobre OllamaClient para mantener la interfaz pública."""

    def __init__(self, model: str = "llama3", base_url: str = "http://localhost:11434"):
        self._ollama = OllamaClient(base_url=base_url, model=model)

    def generate(self, prompt: str, system: str = "") -> str:
        return self._ollama.generate(prompt, system=system)

    def chat(self, messages: list[dict], system: str = "") -> str:
        return self._ollama.chat(messages, system=system)

    def embed(self, text: str) -> list[float]:
        return self._ollama.embed(text)

    def is_running(self) -> bool:
        return self._ollama.is_running()

    def list_models(self) -> list[str]:
        return self._ollama.list_models()
