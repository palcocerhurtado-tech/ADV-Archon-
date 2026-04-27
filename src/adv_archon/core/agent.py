"""Bucle agentico real: LLM → herramienta → LLM … hasta respuesta final."""
import json
import re
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from adv_archon.core.consent import ConsentGate
    from adv_archon.core.memory import Memory
    from adv_archon.integrations.ollama import OllamaClient
    from adv_archon.plugins.loader import PluginLoader
    from adv_archon.tools.files import FilesTool
    from adv_archon.tools.mac_apps import MacAppsTool
    from adv_archon.tools.web import WebTool

MAX_TOOL_ITERATIONS = 6

SYSTEM_PROMPT = """\
Eres Archon, asistente personal de IA que corre 100 % en local usando Ollama.
Hablas siempre en el idioma del usuario (español si escribe en español).

═══════════════════════════════════════════
HERRAMIENTAS — cómo usarlas
═══════════════════════════════════════════
Cuando necesites usar una herramienta responde ÚNICAMENTE con un bloque JSON
delimitado exactamente así (sin texto antes ni después):

```tool
{"tool": "nombre", "params": {"clave": "valor"}}
```

Herramientas disponibles:

  Archivos y búsqueda
  ───────────────────
  read_file        {"path": "/ruta/archivo"}
  write_file       {"path": "/ruta/archivo", "content": "texto"}
  delete_file      {"path": "/ruta/archivo"}
  list_dir         {"path": "/ruta/directorio"}
  search_files     {"query": "patron", "directory": "~"}
  search_memory    {"query": "lo que busco"}

  Memoria personal
  ───────────────────
  remember         {"key": "clave", "value": "valor a recordar"}
  recall           {"query": "qué quiero recordar"}

  Web / Internet
  ───────────────────
  search_web         {"query": "lo que quiero buscar", "max_results": 5}
  browse_url         {"url": "https://ejemplo.com"}
  playwright_browse  {"url": "https://ejemplo.com"}  ← browser real, ideal para tiendas y SPAs con JS

  Aplicaciones Mac
  ───────────────────
  list_running_apps   {}
  list_installed_apps {}
  open_app         {"app": "NombreApp"}
  quit_app         {"app": "NombreApp"}
  screenshot       {"app": "NombreApp"}   ← app es opcional
  type_text        {"app": "NombreApp", "text": "texto a escribir"}
  click_menu       {"app": "NombreApp", "menu": "Archivo", "item": "Guardar"}
  run_shell        {"command": "comando bash"}
  run_applescript  {"script": "código AppleScript", "description": "qué hace"}

═══════════════════════════════════════════
REGLAS ABSOLUTAS
═══════════════════════════════════════════
1. NUNCA hagas cambios en el sistema sin pedir permiso — el sistema de
   consentimiento preguntará al usuario automáticamente, pero nunca actúes
   como si ya tuvieras autorización.
2. Si no sabes algo busca primero en search_memory antes de responder.
3. Cuando uses una herramienta responde SOLO el bloque ```tool … ```.
4. Tras recibir el resultado de la herramienta, continúa con naturalidad.
5. Sé conciso, directo y amigable.
6. NUNCA repitas la misma búsqueda web dos veces. Si search_web ya devolvió
   resultados, sintetiza lo que encontraste aunque sea parcial.
"""


class Agent:
    def __init__(
        self,
        llm: "OllamaClient",
        files: "FilesTool",
        mac: "MacAppsTool",
        memory: "Memory",
        consent: "ConsentGate",
        plugins: "PluginLoader",
        web: "WebTool | None" = None,
    ):
        self.llm = llm
        self.files = files
        self.mac = mac
        self.memory = memory
        self.consent = consent
        self.plugins = plugins
        self.web = web
        self._history: list[dict] = []

    # ------------------------------------------------------------------
    # API pública
    # ------------------------------------------------------------------
    def process(self, user_input: str) -> str:
        """Procesa input del usuario. Devuelve respuesta final en texto."""
        # Enriquecer con contexto de memoria relevante
        ctx = self._memory_context(user_input)
        content = f"{ctx}\n\nUsuario: {user_input}" if ctx else user_input
        self._history.append({"role": "user", "content": content})

        # Añadir hints de plugins al system prompt
        plugin_hints = self.plugins.system_prompt_hints()
        system = SYSTEM_PROMPT + (f"\n\n{plugin_hints}" if plugin_hints else "")

        last_tool_call: dict | None = None
        for _ in range(MAX_TOOL_ITERATIONS):
            response = self.llm.chat(messages=self._history, system=system)
            tool_call = self._extract_tool_call(response)

            if tool_call is None:
                self._history.append({"role": "assistant", "content": response})
                return response

            # Si el LLM repite exactamente la misma tool call, cortar el loop
            if tool_call == last_tool_call:
                self._history.append({"role": "assistant", "content": response})
                self._history.append(
                    {
                        "role": "user",
                        "content": (
                            "Ya ejecutaste esa búsqueda y obtuviste el resultado anterior. "
                            "Resume lo que encontraste y responde al usuario con lo que tienes."
                        ),
                    }
                )
                final = self.llm.chat(messages=self._history, system=system)
                self._history.append({"role": "assistant", "content": final})
                return final
            last_tool_call = tool_call

            # Ejecutar herramienta
            tool_result = self._run_tool(tool_call["tool"], tool_call.get("params", {}))

            # Guardar en historial como turno asistente + respuesta de sistema
            self._history.append({"role": "assistant", "content": response})
            self._history.append(
                {
                    "role": "user",
                    "content": f"[Resultado de {tool_call['tool']}]\n{tool_result}",
                }
            )

        # Si se agotaron las iteraciones, pedir respuesta final
        self._history.append(
            {"role": "user", "content": "Resume lo que has hecho y responde al usuario."}
        )
        final = self.llm.chat(messages=self._history, system=system)
        self._history.append({"role": "assistant", "content": final})
        return final

    def reset(self):
        self._history.clear()

    # ------------------------------------------------------------------
    # Extracción de tool call
    # ------------------------------------------------------------------
    def _extract_tool_call(self, response: str) -> Optional[dict]:
        # Buscar bloque ```tool … ```
        match = re.search(r"```tool\s*(\{.*?\})\s*```", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Fallback: JSON bare que empiece con {"tool":
        stripped = response.strip()
        if stripped.startswith("{") and '"tool"' in stripped:
            try:
                return json.loads(stripped)
            except json.JSONDecodeError:
                pass

        return None

    # ------------------------------------------------------------------
    # Despacho de herramientas
    # ------------------------------------------------------------------
    def _run_tool(self, tool: str, params: dict) -> str:
        try:
            # ── Web ───────────────────────────────────────────────────
            if tool == "search_web":
                if self.web is None:
                    return "Búsqueda web no disponible (instala ddgs)."
                return self.web.search(params["query"], params.get("max_results", 5))
            if tool == "browse_url":
                if self.web is None:
                    return "Navegación web no disponible (instala ddgs)."
                return self.web.fetch(params["url"])
            if tool == "playwright_browse":
                if self.web is None:
                    return "Herramienta web no disponible."
                return self.web.playwright_browse(params["url"])

            # ── Archivos ──────────────────────────────────────────────
            if tool == "read_file":
                return self.files.read(params["path"])
            if tool == "write_file":
                ok = self.files.write(params["path"], params["content"])
                return "Archivo escrito." if ok else "Escritura cancelada por el usuario."
            if tool == "delete_file":
                ok = self.files.delete(params["path"])
                return "Archivo eliminado." if ok else "Eliminación cancelada."
            if tool == "list_dir":
                items = self.files.list_dir(params.get("path", "~"))
                rows = [
                    f"{'[DIR] ' if i['type'] == 'dir' else '[FILE]'} {i['name']}"
                    for i in items
                ]
                return "\n".join(rows) or "(vacío)"
            if tool == "search_files":
                results = self.files.search_files(
                    params["query"], params.get("directory", "~")
                )
                return "\n".join(results) if results else "Sin resultados."
            if tool == "search_memory":
                hits = self.memory.search(params["query"])
                if not hits:
                    return "No encontré nada relevante en la memoria indexada."
                parts = [f"[{h['filepath']}]\n{h['content'][:400]}" for h in hits]
                return "\n\n---\n\n".join(parts)

            # ── Memoria personal ──────────────────────────────────────
            if tool == "remember":
                self.memory.remember(params["key"], params["value"])
                return "Guardado en memoria."
            if tool == "recall":
                mems = self.memory.recall(params["query"])
                return "\n".join(mems) if mems else "No encontré recuerdos relevantes."

            # ── Aplicaciones Mac ──────────────────────────────────────
            if tool == "list_running_apps":
                apps = self.mac.list_running_apps()
                return "Apps abiertas: " + (", ".join(apps) or "ninguna")
            if tool == "list_installed_apps":
                apps = self.mac.list_installed_apps()
                return "Apps instaladas: " + ", ".join(apps[:30])
            if tool == "open_app":
                ok = self.mac.open_app(params["app"])
                return "App abierta." if ok else "No se abrió (cancelado o error)."
            if tool == "quit_app":
                ok = self.mac.quit_app(params["app"])
                return "App cerrada." if ok else "No se cerró (cancelado o error)."
            if tool == "screenshot":
                path = self.mac.take_screenshot(params.get("app"))
                return f"Screenshot guardado en {path}." if path else "No se pudo tomar la captura."
            if tool == "type_text":
                ok = self.mac.type_text(params["app"], params["text"])
                return "Texto escrito." if ok else "Cancelado."
            if tool == "click_menu":
                ok = self.mac.click_menu_item(params["app"], params["menu"], params["item"])
                return "Clic realizado." if ok else "Cancelado."
            if tool == "run_shell":
                ok, out = self.mac.run_shell(params["command"])
                return out or ("Ejecutado." if ok else "Error.")
            if tool == "run_applescript":
                ok, out = self.mac.run_applescript(params["script"], params.get("description", "AppleScript"))
                return out or ("Ejecutado." if ok else "Error.")

            # ── Plugins ───────────────────────────────────────────────
            found, result = self.plugins.execute_by_action(tool, **params)
            if found:
                return str(result)

            return f"Herramienta desconocida: '{tool}'."

        except KeyError as e:
            return f"Parámetro requerido faltante: {e}"
        except Exception as e:
            return f"Error ejecutando '{tool}': {e}"

    # ------------------------------------------------------------------
    # Contexto de memoria para enriquecer cada turno
    # ------------------------------------------------------------------
    def _memory_context(self, query: str) -> str:
        if self.memory.files_indexed() == 0:
            return ""
        hits = self.memory.search(query, n_results=3)
        if not hits:
            return ""
        parts = [f"[{h['filepath']}]: {h['content'][:200]}" for h in hits]
        return "Contexto relevante de tus archivos:\n" + "\n".join(parts)
