"""Herramienta de sistema de archivos — acceso completo con gate de consentimiento."""
import mimetypes
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

if TYPE_CHECKING:
    from adv_archon.core.consent import ConsentGate
    from adv_archon.core.memory import Memory

TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".jsx", ".tsx", ".json", ".yaml", ".yml",
    ".toml", ".ini", ".cfg", ".env", ".sh", ".bash", ".zsh", ".fish",
    ".html", ".css", ".scss", ".xml", ".csv", ".log", ".rst", ".tex",
    ".swift", ".kt", ".java", ".cpp", ".c", ".h", ".go", ".rs",
    ".rb", ".php", ".sql", ".graphql", ".makefile", ".dockerfile",
    ".vue", ".svelte", ".astro", ".mdx",
}

SKIP_DIRS = {
    ".git", "node_modules", "__pycache__", ".venv", "venv", "env",
    ".DS_Store", "Library", "System", "Applications", ".Trash",
    "Pictures", "Music", "Movies",  # grandes binarios
}


class FilesTool:
    def __init__(
        self,
        consent: Optional["ConsentGate"] = None,
        memory: Optional["Memory"] = None,
    ):
        self.consent = consent
        self.memory = memory

    # ------------------------------------------------------------------
    # Lectura (sin consentimiento — solo leer no modifica nada)
    # ------------------------------------------------------------------
    def read(self, path: str) -> str:
        p = Path(path).expanduser().resolve()
        try:
            return p.read_text(encoding="utf-8", errors="replace")
        except Exception as e:
            return f"[Error leyendo {path}]: {e}"

    def list_dir(self, path: str = "~") -> list[dict]:
        p = Path(path).expanduser().resolve()
        items = []
        try:
            for item in sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name.lower())):
                items.append(
                    {
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else 0,
                        "path": str(item),
                    }
                )
        except PermissionError:
            pass
        return items

    def search_files(self, query: str, directory: str = "~", max_results: int = 50) -> list[str]:
        base = Path(directory).expanduser().resolve()
        matches = []
        try:
            for p in base.rglob(f"*{query}*"):
                if not any(part in SKIP_DIRS for part in p.parts):
                    matches.append(str(p))
                    if len(matches) >= max_results:
                        break
        except PermissionError:
            pass
        return matches

    # ------------------------------------------------------------------
    # Escritura (requiere consentimiento)
    # ------------------------------------------------------------------
    def write(self, path: str, content: str) -> bool:
        p = Path(path).expanduser().resolve()
        if self.consent:
            preview = content[:300] + ("…" if len(content) > 300 else "")
            approved = self.consent.request(
                action_id=f"write:{path}",
                title=f"Escribir archivo: {path}",
                details=f"Contenido (primeros 300 chars):\n{preview}",
            )
            if not approved:
                return False
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return True

    def delete(self, path: str) -> bool:
        p = Path(path).expanduser().resolve()
        if self.consent:
            approved = self.consent.request(
                action_id=f"delete:{path}",
                title=f"ELIMINAR archivo: {path}",
                details="⚠️  Esta acción es irreversible.",
                allow_remember=False,
            )
            if not approved:
                return False
        p.unlink(missing_ok=True)
        return True

    # ------------------------------------------------------------------
    # Indexación para RAG
    # ------------------------------------------------------------------
    def index_directory(
        self,
        directory: str = "~",
        progress_callback: Optional[Callable[[int, str], None]] = None,
    ) -> int:
        if not self.memory:
            return 0

        base = Path(directory).expanduser().resolve()
        count = 0

        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            if p.suffix.lower() not in TEXT_EXTENSIONS:
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                if len(content.strip()) < 30:
                    continue
                self.memory.index_file(p, content)
                count += 1
                if progress_callback:
                    progress_callback(count, str(p))
            except Exception:
                pass

        return count
