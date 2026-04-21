"""Sistema de consentimiento — NINGUNA acción destructiva ocurre sin aprobación explícita."""
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm

console = Console()


class ConsentGate:
    """Intercepta toda acción con efecto en el sistema y pide permiso al usuario."""

    def __init__(self):
        self._session_approvals: set[str] = set()
        self.deny_all = False  # modo seguro de emergencia

    def request(
        self,
        action_id: str,
        title: str,
        details: str = "",
        allow_remember: bool = True,
    ) -> bool:
        """
        Muestra al usuario lo que Archon quiere hacer y espera una respuesta.
        Devuelve True solo si el usuario aprueba explícitamente.
        """
        if self.deny_all:
            console.print(f"[dim]Acción bloqueada (modo seguro): {title}[/dim]")
            return False

        if action_id in self._session_approvals:
            console.print(f"[dim]✓ Autorización de sesión recordada para: {title}[/dim]")
            return True

        body = f"[bold yellow]{title}[/bold yellow]"
        if details:
            body += f"\n\n[dim]{details}[/dim]"
        body += "\n\n[bold red]Archon necesita tu permiso para continuar.[/bold red]"

        console.print()
        console.print(
            Panel(body, title="[bold]🔐  CONSENTIMIENTO REQUERIDO[/bold]", border_style="yellow")
        )

        approved = Confirm.ask("[bold]¿Autorizas esta acción?[/bold]", default=False)

        if approved and allow_remember:
            remember = Confirm.ask(
                "¿Recordar esta autorización durante toda la sesión?", default=False
            )
            if remember:
                self._session_approvals.add(action_id)

        if not approved:
            console.print("[red]Acción cancelada por el usuario.[/red]\n")

        return approved

    def revoke_session(self, action_id: str):
        self._session_approvals.discard(action_id)

    def revoke_all_session(self):
        self._session_approvals.clear()
