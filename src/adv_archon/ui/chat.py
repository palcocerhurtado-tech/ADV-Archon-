"""Interfaz de chat en lenguaje natural — terminal rico con Rich."""
import time
from typing import TYPE_CHECKING

from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text
from rich.theme import Theme

if TYPE_CHECKING:
    from adv_archon.core.agent import Agent
    from adv_archon.integrations.ollama import OllamaClient

_THEME = Theme(
    {
        "archon": "bold cyan",
        "user_label": "bold green",
        "sys": "bold yellow",
        "danger": "bold red",
        "dim": "dim white",
    }
)

BANNER = """\
[bold cyan]
    ╔══════════════════════════════════════════╗
    ║       A D V  ·  A R C H O N             ║
    ║   Asistente personal IA — 100 % local   ║
    ║   Motor: Ollama  ·  Sin nube            ║
    ╚══════════════════════════════════════════╝
[/bold cyan]"""

HELP_TEXT = """\
[bold]Comandos especiales:[/bold]
  [cyan]indexar [directorio][/cyan]  — Indexa archivos para que Archon aprenda de ellos
  [cyan]modelos[/cyan]               — Lista los modelos Ollama disponibles
  [cyan]modelo <nombre>[/cyan]       — Cambia el modelo activo
  [cyan]memoria[/cyan]               — Muestra cuántos fragmentos están indexados
  [cyan]limpiar[/cyan]               — Borra el historial de conversación
  [cyan]seguro[/cyan]                — Activa modo seguro (deniega todas las acciones)
  [cyan]permisos[/cyan]              — Revoca todas las autorizaciones de sesión
  [cyan]ayuda[/cyan]                 — Muestra este menú
  [cyan]salir[/cyan]                 — Cierra Archon
"""

console = Console(theme=_THEME)


class ChatUI:
    def __init__(self, agent: "Agent", ollama: "OllamaClient"):
        self.agent = agent
        self.ollama = ollama

    # ------------------------------------------------------------------
    # Bucle principal
    # ------------------------------------------------------------------
    def start(self):
        console.clear()
        console.print(BANNER)
        self._check_ollama()
        console.print(
            "[dim]Escribe [cyan]ayuda[/cyan] para ver los comandos disponibles.[/dim]\n"
        )

        while True:
            try:
                raw = Prompt.ask("[bold green]Tú[/bold green]").strip()
            except (KeyboardInterrupt, EOFError):
                self._handle_interrupt()
                continue

            if not raw:
                continue

            lower = raw.lower()

            # ── Comandos del sistema ──────────────────────────────────
            if lower in ("salir", "exit", "quit", "bye", "adios", "adiós"):
                console.print("\n[archon]Archon:[/archon] ¡Hasta pronto! Que tengas un gran día.\n")
                break

            if lower in ("ayuda", "help"):
                console.print(HELP_TEXT)
                continue

            if lower.startswith("indexar"):
                parts = raw.split(maxsplit=1)
                self._cmd_index(parts[1] if len(parts) > 1 else "~")
                continue

            if lower == "modelos":
                self._cmd_list_models()
                continue

            if lower.startswith("modelo "):
                self._cmd_change_model(raw.split(maxsplit=1)[1])
                continue

            if lower == "memoria":
                n = self.agent.memory.files_indexed()
                console.print(f"[sys]Fragmentos indexados en memoria: {n}[/sys]")
                continue

            if lower == "limpiar":
                self.agent.reset()
                console.print("[sys]Historial de conversación borrado.[/sys]")
                continue

            if lower == "seguro":
                self.agent.consent.deny_all = True
                console.print("[danger]Modo seguro activado. Archon no podrá realizar cambios.[/danger]")
                continue

            if lower == "permisos":
                self.agent.consent.revoke_all_session()
                console.print("[sys]Todas las autorizaciones de sesión revocadas.[/sys]")
                continue

            # ── Pregunta al agente ────────────────────────────────────
            console.print()
            with console.status("[archon]Archon está pensando…[/archon]", spinner="dots"):
                try:
                    response = self.agent.process(raw)
                except Exception as e:
                    response = f"[Error interno]: {e}"

            console.print(Rule(style="dim"))
            console.print("[archon]Archon:[/archon]")
            try:
                console.print(Markdown(response))
            except Exception:
                console.print(response)
            console.print()

    # ------------------------------------------------------------------
    # Comandos
    # ------------------------------------------------------------------
    def _check_ollama(self):
        console.print("[sys]Conectando con Ollama…[/sys]")
        if self.ollama.is_running():
            models = self.ollama.list_models()
            model_list = ", ".join(models[:5]) or "(ninguno)"
            console.print(f"[sys]✓ Ollama activo · Modelo: [cyan]{self.ollama.model}[/cyan]")
            console.print(f"[sys]  Modelos disponibles: {model_list}[/sys]\n")
        else:
            console.print(
                "[danger]✗ No se puede conectar con Ollama.[/danger]\n"
                "[dim]  Asegúrate de que Ollama está corriendo: [cyan]ollama serve[/cyan][/dim]\n"
            )

    def _cmd_index(self, directory: str):
        console.print(f"[sys]Indexando archivos en: [cyan]{directory}[/cyan][/sys]")
        console.print("[dim]  (puede tardar varios minutos en directorios grandes)[/dim]")

        count = [0]
        last_print = [time.time()]

        def progress(n: int, path: str):
            count[0] = n
            now = time.time()
            if now - last_print[0] > 2.0:
                console.print(f"  [dim][{n}] …{path[-60:]}[/dim]")
                last_print[0] = now

        total = self.agent.files.index_directory(directory, progress_callback=progress)
        console.print(f"[sys]✓ Indexados [cyan]{total}[/cyan] archivos de {directory}[/sys]\n")

    def _cmd_list_models(self):
        models = self.ollama.list_models()
        if models:
            console.print("[sys]Modelos Ollama disponibles:[/sys]")
            for m in models:
                marker = " ◄ activo" if m == self.ollama.model else ""
                console.print(f"  [cyan]{m}[/cyan]{marker}")
        else:
            console.print("[danger]No se encontraron modelos. ¿Has descargado alguno con ollama pull?[/danger]")
        console.print()

    def _cmd_change_model(self, model_name: str):
        self.ollama.model = model_name.strip()
        console.print(f"[sys]Modelo cambiado a: [cyan]{self.ollama.model}[/cyan][/sys]\n")

    def _handle_interrupt(self):
        console.print("\n[dim]  (usa [cyan]salir[/cyan] para cerrar Archon)[/dim]")
