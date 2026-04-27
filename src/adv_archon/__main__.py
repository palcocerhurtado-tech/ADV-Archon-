"""Punto de entrada: python -m adv_archon  o  archon (si está instalado)."""
from adv_archon.core.config import Config
from adv_archon.core.consent import ConsentGate
from adv_archon.core.memory import Memory
from adv_archon.core.agent import Agent
from adv_archon.integrations.ollama import OllamaClient
from adv_archon.tools.files import FilesTool
from adv_archon.tools.mac_apps import MacAppsTool
from adv_archon.tools.web import WebTool
from adv_archon.plugins.loader import PluginLoader
from adv_archon.ui.chat import ChatUI


def main():
    cfg = Config.from_env()

    ollama = OllamaClient(base_url=cfg.ollama_url, model=cfg.ollama_model)
    consent = ConsentGate()
    memory = Memory(db_path=cfg.memory_path)
    memory.ollama = ollama  # habilita embeddings semánticos

    files = FilesTool(consent=consent, memory=memory)
    mac = MacAppsTool(consent=consent)
    web = WebTool()

    plugins = PluginLoader()
    plugins.load_directory(consent=consent, memory=memory)

    agent = Agent(
        llm=ollama,
        files=files,
        mac=mac,
        memory=memory,
        consent=consent,
        plugins=plugins,
        web=web,
    )

    if cfg.index_on_start:
        from rich.console import Console
        Console().print(
            f"[yellow]Indexando {cfg.index_directory} al iniciar (INDEX_ON_START=true)…[/yellow]"
        )
        files.index_directory(cfg.index_directory)

    ui = ChatUI(agent=agent, ollama=ollama)
    ui.start()


if __name__ == "__main__":
    main()
