"""Control de aplicaciones macOS mediante AppleScript — todo con consentimiento previo."""
import subprocess
import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from adv_archon.core.consent import ConsentGate


class MacAppsTool:
    def __init__(self, consent: Optional["ConsentGate"] = None):
        self.consent = consent

    # ------------------------------------------------------------------
    # AppleScript interno
    # ------------------------------------------------------------------
    def _osascript(self, script: str) -> tuple[str, str]:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip(), result.stderr.strip()

    # ------------------------------------------------------------------
    # Información (sin consentimiento)
    # ------------------------------------------------------------------
    def list_running_apps(self) -> list[str]:
        out, _ = self._osascript(
            'tell application "System Events" to get name of every application process '
            "whose background only is false"
        )
        return [a.strip() for a in out.split(",") if a.strip()]

    def list_installed_apps(self) -> list[str]:
        apps = []
        for d in ["/Applications", str(Path.home() / "Applications")]:
            p = Path(d)
            if p.exists():
                apps.extend(f.stem for f in p.glob("*.app"))
        return sorted(set(apps))

    def get_frontmost_app(self) -> str:
        out, _ = self._osascript(
            'tell application "System Events" to get name of first application process '
            "whose frontmost is true"
        )
        return out

    def get_window_titles(self, app_name: str) -> list[str]:
        script = f"""
tell application "System Events"
    tell process "{app_name}"
        set t to {{}}
        repeat with w in windows
            set end of t to name of w
        end repeat
        return t
    end tell
end tell
"""
        out, _ = self._osascript(script)
        return [w.strip() for w in out.split(",") if w.strip()]

    # ------------------------------------------------------------------
    # Acciones (requieren consentimiento)
    # ------------------------------------------------------------------
    def open_app(self, app_name: str) -> bool:
        if not self._ask(f"open_app:{app_name}", f"Abrir aplicación: {app_name}"):
            return False
        r = subprocess.run(["open", "-a", app_name], capture_output=True, text=True)
        return r.returncode == 0

    def quit_app(self, app_name: str) -> bool:
        if not self._ask(f"quit_app:{app_name}", f"Cerrar aplicación: {app_name}"):
            return False
        _, err = self._osascript(f'tell application "{app_name}" to quit')
        return not err

    def take_screenshot(self, app_name: Optional[str] = None) -> Optional[str]:
        label = f"captura de {app_name}" if app_name else "captura de pantalla"
        if not self._ask("screenshot", f"Tomar {label}"):
            return None
        out_dir = Path.home() / ".adv_archon" / "screenshots"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = str(out_dir / f"screenshot_{int(time.time())}.png")
        if app_name:
            self._osascript(f'tell application "{app_name}" to activate')
            time.sleep(0.5)
        r = subprocess.run(["screencapture", "-x", out_path], capture_output=True, text=True)
        return out_path if r.returncode == 0 else None

    def type_text(self, app_name: str, text: str) -> bool:
        preview = text[:80] + ("…" if len(text) > 80 else "")
        if not self._ask(
            f"type_text:{app_name}",
            f"Escribir texto en {app_name}",
            details=f'Texto: "{preview}"',
        ):
            return False
        script = f"""
tell application "{app_name}" to activate
tell application "System Events"
    keystroke "{text}"
end tell
"""
        _, err = self._osascript(script)
        return not err

    def click_menu_item(self, app_name: str, menu: str, item: str) -> bool:
        if not self._ask(
            f"menu:{app_name}:{menu}:{item}",
            f"Clic en menú {menu} › {item} en {app_name}",
        ):
            return False
        script = f"""
tell application "{app_name}" to activate
tell application "System Events"
    tell process "{app_name}"
        click menu item "{item}" of menu "{menu}" of menu bar 1
    end tell
end tell
"""
        _, err = self._osascript(script)
        return not err

    def run_applescript(self, script: str, description: str) -> tuple[bool, str]:
        if not self._ask(
            "custom_applescript",
            description,
            details=f"Script AppleScript:\n{script}",
            allow_remember=False,
        ):
            return False, "Acción denegada."
        out, err = self._osascript(script)
        if err:
            return False, err
        return True, out

    def run_shell(self, command: str) -> tuple[bool, str]:
        if not self._ask(
            "shell_command",
            "Ejecutar comando de terminal",
            details=f"Comando: `{command}`\n\n⚠️ Esto ejecuta código directamente en tu sistema.",
            allow_remember=False,
        ):
            return False, "Comando denegado."
        try:
            r = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=60
            )
            return r.returncode == 0, r.stdout or r.stderr
        except subprocess.TimeoutExpired:
            return False, "Tiempo de espera agotado."
        except Exception as e:
            return False, str(e)

    # ------------------------------------------------------------------
    # Helpers internos
    # ------------------------------------------------------------------
    def _ask(
        self,
        action_id: str,
        title: str,
        details: str = "",
        allow_remember: bool = True,
    ) -> bool:
        if not self.consent:
            return False
        return self.consent.request(
            action_id=action_id,
            title=title,
            details=details,
            allow_remember=allow_remember,
        )
