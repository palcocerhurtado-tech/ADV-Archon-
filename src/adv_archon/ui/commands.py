"""Comandos de utilidad para la CLI."""


class Commands:
    @staticmethod
    def help() -> str:
        return (
            "ADV Archon v0.2.0 — asistente IA personal, 100 % local.\n"
            "Uso: python -m adv_archon\n"
            "Comandos en chat: indexar, modelos, modelo, memoria, limpiar, seguro, ayuda, salir"
        )

    @staticmethod
    def status(ollama_running: bool, files_indexed: int, model: str) -> str:
        ollama_str = "activo" if ollama_running else "INACTIVO"
        return (
            f"Ollama: {ollama_str} · Modelo: {model} · "
            f"Fragmentos indexados: {files_indexed}"
        )
