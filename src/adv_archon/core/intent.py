"""Representación de intención — el análisis real lo hace el LLM en el bucle del agente."""
from dataclasses import dataclass, field


@dataclass
class Intent:
    raw: str
    action: str = ""
    params: dict = field(default_factory=dict)

    @staticmethod
    def from_text(text: str) -> "Intent":
        return Intent(raw=text, action=text)
