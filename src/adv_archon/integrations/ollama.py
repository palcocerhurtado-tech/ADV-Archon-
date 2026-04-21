"""Cliente HTTP real para Ollama — único motor LLM de Archon."""
import json
from typing import Generator, Optional
import httpx


class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434", model: str = "llama3"):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self._client = httpx.Client(timeout=300.0)

    # ------------------------------------------------------------------
    # Comprobación de estado
    # ------------------------------------------------------------------
    def is_running(self) -> bool:
        try:
            r = self._client.get(f"{self.base_url}/api/tags", timeout=5.0)
            return r.status_code == 200
        except Exception:
            return False

    def list_models(self) -> list[str]:
        try:
            r = self._client.get(f"{self.base_url}/api/tags")
            r.raise_for_status()
            return [m["name"] for m in r.json().get("models", [])]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Generación de texto (prompt único)
    # ------------------------------------------------------------------
    def generate(self, prompt: str, system: str = "") -> str:
        payload: dict = {"model": self.model, "prompt": prompt, "stream": False}
        if system:
            payload["system"] = system
        r = self._client.post(f"{self.base_url}/api/generate", json=payload)
        r.raise_for_status()
        return r.json()["response"]

    # ------------------------------------------------------------------
    # Chat (historial de mensajes)
    # ------------------------------------------------------------------
    def chat(self, messages: list[dict], system: str = "") -> str:
        payload: dict = {"model": self.model, "messages": messages, "stream": False}
        if system:
            payload["system"] = system
        r = self._client.post(f"{self.base_url}/api/chat", json=payload)
        r.raise_for_status()
        return r.json()["message"]["content"]

    def chat_stream(self, messages: list[dict], system: str = "") -> Generator[str, None, None]:
        payload: dict = {"model": self.model, "messages": messages, "stream": True}
        if system:
            payload["system"] = system
        with self._client.stream("POST", f"{self.base_url}/api/chat", json=payload) as r:
            for line in r.iter_lines():
                if line:
                    data = json.loads(line)
                    if not data.get("done", False):
                        yield data["message"]["content"]

    # ------------------------------------------------------------------
    # Embeddings para RAG
    # ------------------------------------------------------------------
    def embed(self, text: str) -> list[float]:
        payload = {"model": self.model, "prompt": text}
        r = self._client.post(f"{self.base_url}/api/embeddings", json=payload)
        r.raise_for_status()
        return r.json()["embedding"]

    def close(self):
        self._client.close()
