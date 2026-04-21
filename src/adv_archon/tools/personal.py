"""Memoria personal en RAM (sin persistencia) — para datos ligeros de sesión."""


class PersonalTool:
    """Almacén clave-valor volátil. Para persistencia real usa Memory (ChromaDB)."""

    def __init__(self):
        self._store: dict[str, str] = {}

    def remember(self, key: str, value: str):
        self._store[key] = value

    def recall(self, key: str) -> str | None:
        return self._store.get(key)

    def forget(self, key: str):
        self._store.pop(key, None)

    def all_keys(self) -> list[str]:
        return list(self._store.keys())
