"""Web search (DuckDuckGo via ddgs) and page fetch tool."""
import re

import httpx

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS  # fallback: older installs


class WebTool:
    def search(self, query: str, max_results: int = 5) -> str:
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            if not results:
                return "Sin resultados para esa búsqueda."
            lines = []
            for r in results:
                title = r.get("title", "")
                href = r.get("href", "")
                body = r.get("body", "")[:200]
                lines.append(f"**{title}**\n{href}\n{body}")
            return "\n\n".join(lines)
        except Exception as e:
            return f"Error en búsqueda web: {e}"

    def fetch(self, url: str) -> str:
        try:
            headers = {"User-Agent": "Mozilla/5.0 (compatible; Archon/1.0)"}
            r = httpx.get(url, timeout=15, follow_redirects=True, headers=headers)
            text = re.sub(r"<[^>]+>", " ", r.text)
            text = re.sub(r"\s+", " ", text).strip()
            return text[:4000]
        except Exception as e:
            return f"Error cargando {url}: {e}"
