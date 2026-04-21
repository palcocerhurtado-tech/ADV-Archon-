"""Memoria vectorial persistente con ChromaDB — aprende de tus archivos."""
import hashlib
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import chromadb

if TYPE_CHECKING:
    from adv_archon.integrations.ollama import OllamaClient


class Memory:
    CHUNK_SIZE = 800
    CHUNK_OVERLAP = 150

    def __init__(self, db_path: str = "~/.adv_archon/memory"):
        resolved = Path(db_path).expanduser()
        resolved.mkdir(parents=True, exist_ok=True)
        self._db = chromadb.PersistentClient(path=str(resolved))
        self._files = self._db.get_or_create_collection("files")
        self._personal = self._db.get_or_create_collection("personal")
        self.ollama: Optional["OllamaClient"] = None  # inyectado después de __init__

    # ------------------------------------------------------------------
    # Indexación de archivos (RAG)
    # ------------------------------------------------------------------
    def index_file(self, filepath: Path, content: str):
        file_id = hashlib.md5(str(filepath).encode()).hexdigest()
        chunks = self._chunk(content)

        ids, docs, metas, embeddings = [], [], [], []
        for i, chunk in enumerate(chunks):
            ids.append(f"{file_id}_{i}")
            docs.append(chunk)
            metas.append({"filepath": str(filepath), "chunk": i})
            if self.ollama:
                try:
                    embeddings.append(self.ollama.embed(chunk))
                except Exception:
                    pass

        if embeddings and len(embeddings) == len(ids):
            self._files.upsert(ids=ids, documents=docs, metadatas=metas, embeddings=embeddings)
        else:
            self._files.upsert(ids=ids, documents=docs, metadatas=metas)

    def search(self, query: str, n_results: int = 5) -> list[dict]:
        try:
            count = self._files.count()
            if count == 0:
                return []
            n = min(n_results, count)
            if self.ollama:
                try:
                    emb = self.ollama.embed(query)
                    res = self._files.query(query_embeddings=[emb], n_results=n)
                except Exception:
                    res = self._files.query(query_texts=[query], n_results=n)
            else:
                res = self._files.query(query_texts=[query], n_results=n)

            return [
                {"content": doc, "filepath": res["metadatas"][0][i]["filepath"]}
                for i, doc in enumerate(res["documents"][0])
            ]
        except Exception:
            return []

    def files_indexed(self) -> int:
        try:
            return self._files.count()
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Memoria personal (clave-valor semántico)
    # ------------------------------------------------------------------
    def remember(self, key: str, value: str):
        self._personal.upsert(
            ids=[key],
            documents=[value],
            metadatas=[{"type": "personal", "key": key}],
        )

    def recall(self, query: str, n_results: int = 3) -> list[str]:
        try:
            count = self._personal.count()
            if count == 0:
                return []
            n = min(n_results, count)
            res = self._personal.query(query_texts=[query], n_results=n)
            return res["documents"][0]
        except Exception:
            return []

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    def _chunk(self, text: str) -> list[str]:
        chunks, start = [], 0
        while start < len(text):
            chunks.append(text[start : start + self.CHUNK_SIZE])
            start += self.CHUNK_SIZE - self.CHUNK_OVERLAP
        return chunks or [""]
