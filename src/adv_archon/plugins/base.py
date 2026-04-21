"""Clase base para todos los plugins de Archon."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from adv_archon.core.consent import ConsentGate
    from adv_archon.core.memory import Memory


@dataclass
class PluginAction:
    name: str
    description: str
    parameters: dict[str, str] = field(default_factory=dict)
    # parámetros requeridos para que el agente sepa cómo llamarla
    required: list[str] = field(default_factory=list)


class BasePlugin(ABC):
    """Hereda de esta clase para crear un plugin para Archon.

    Crea un archivo .py en ~/.adv_archon/plugins/ que defina una subclase.
    Archon la cargará automáticamente al iniciar.
    """

    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    def __init__(
        self,
        consent: "ConsentGate | None" = None,
        memory: "Memory | None" = None,
    ):
        self.consent = consent
        self.memory = memory

    @abstractmethod
    def get_actions(self) -> list[PluginAction]:
        """Lista de acciones que expone este plugin al agente."""

    @abstractmethod
    def execute(self, action: str, **kwargs) -> Any:
        """Ejecuta una acción por nombre."""

    def system_prompt_hint(self) -> str:
        """Texto adicional a inyectar en el system prompt del agente."""
        actions = self.get_actions()
        lines = [f"Plugin disponible: {self.name} — {self.description}"]
        for a in actions:
            params = ", ".join(f"{k}: {v}" for k, v in a.parameters.items())
            lines.append(f'  - {a.name}({params}): {a.description}')
        return "\n".join(lines)
