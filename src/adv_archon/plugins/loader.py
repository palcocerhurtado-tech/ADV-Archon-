"""Cargador dinámico de plugins desde ~/.adv_archon/plugins/"""
import importlib.util
from pathlib import Path
from typing import TYPE_CHECKING, Any

from .base import BasePlugin, PluginAction

if TYPE_CHECKING:
    from adv_archon.core.consent import ConsentGate
    from adv_archon.core.memory import Memory


class PluginLoader:
    def __init__(self):
        self._plugins: dict[str, BasePlugin] = {}
        self._default_dir = Path.home() / ".adv_archon" / "plugins"
        self._default_dir.mkdir(parents=True, exist_ok=True)

    # ------------------------------------------------------------------
    # Registro y carga
    # ------------------------------------------------------------------
    def register(self, plugin: BasePlugin):
        self._plugins[plugin.name] = plugin

    def load_directory(
        self,
        directory: Path | None = None,
        consent: "ConsentGate | None" = None,
        memory: "Memory | None" = None,
    ) -> list[str]:
        """Carga todos los plugins .py de un directorio. Devuelve lista de nombres cargados."""
        path = directory or self._default_dir
        loaded = []
        for py_file in sorted(path.glob("*.py")):
            if py_file.name.startswith("_"):
                continue
            try:
                spec = importlib.util.spec_from_file_location(py_file.stem, py_file)
                if spec is None or spec.loader is None:
                    continue
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)  # type: ignore[union-attr]
                for attr_name in dir(module):
                    cls = getattr(module, attr_name)
                    if (
                        isinstance(cls, type)
                        and issubclass(cls, BasePlugin)
                        and cls is not BasePlugin
                        and cls.name
                    ):
                        instance = cls(consent=consent, memory=memory)
                        self.register(instance)
                        loaded.append(cls.name)
            except Exception as e:
                print(f"[Plugin] Error cargando {py_file.name}: {e}")
        return loaded

    # ------------------------------------------------------------------
    # Ejecución
    # ------------------------------------------------------------------
    def execute(self, plugin_name: str, action: str, **kwargs) -> Any:
        if plugin_name not in self._plugins:
            raise ValueError(f"Plugin '{plugin_name}' no encontrado")
        return self._plugins[plugin_name].execute(action, **kwargs)

    def execute_by_action(self, action_name: str, **kwargs) -> tuple[bool, Any]:
        """Busca la acción en todos los plugins y la ejecuta."""
        for plugin in self._plugins.values():
            for a in plugin.get_actions():
                if a.name == action_name:
                    return True, plugin.execute(action_name, **kwargs)
        return False, None

    # ------------------------------------------------------------------
    # Introspección
    # ------------------------------------------------------------------
    @property
    def plugins(self) -> dict[str, BasePlugin]:
        return self._plugins

    def all_actions(self) -> dict[str, list[PluginAction]]:
        return {name: p.get_actions() for name, p in self._plugins.items()}

    def system_prompt_hints(self) -> str:
        hints = [p.system_prompt_hint() for p in self._plugins.values() if p.system_prompt_hint()]
        return "\n\n".join(hints)
