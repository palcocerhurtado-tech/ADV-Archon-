"""Integración Gemini — deshabilitada. Archon usa exclusivamente Ollama."""

# Este archivo se mantiene como stub para no romper imports existentes.


class GeminiClient:
    def generate(self, *args, **kwargs) -> str:
        raise NotImplementedError(
            "Gemini no está habilitado. Archon usa exclusivamente Ollama."
        )
