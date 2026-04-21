"""Configuración de Archon — cargada desde variables de entorno o .env"""
import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Config:
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "llama3"
    memory_path: str = "~/.adv_archon/memory"
    plugins_path: str = "~/.adv_archon/plugins"
    screenshots_path: str = "~/.adv_archon/screenshots"
    index_on_start: bool = False
    index_directory: str = "~"

    @classmethod
    def from_env(cls) -> "Config":
        return cls(
            ollama_url=os.getenv("OLLAMA_URL", "http://localhost:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3"),
            memory_path=os.getenv("MEMORY_PATH", "~/.adv_archon/memory"),
            plugins_path=os.getenv("PLUGINS_PATH", "~/.adv_archon/plugins"),
            screenshots_path=os.getenv("SCREENSHOTS_PATH", "~/.adv_archon/screenshots"),
            index_on_start=os.getenv("INDEX_ON_START", "false").lower() == "true",
            index_directory=os.getenv("INDEX_DIRECTORY", "~"),
        )
