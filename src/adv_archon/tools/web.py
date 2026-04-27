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

    def playwright_browse(self, url: str) -> str:
        """Navega con Chromium real — funciona con SPAs, tiendas y páginas con JS."""
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            return (
                "Playwright no está instalado. Ejecuta en terminal:\n"
                "  uv tool install adv-archon --with ddgs --with playwright\n"
                "  playwright install chromium"
            )
        try:
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True)
                page = browser.new_page(
                    user_agent=(
                        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/122.0.0.0 Safari/537.36"
                    )
                )
                page.goto(url, wait_until="networkidle", timeout=30000)
                text = page.evaluate("() => document.body.innerText")
                browser.close()
                if not text or not text.strip():
                    return "Página cargada pero sin texto visible extraíble."
                return text.strip()[:5000]
        except Exception as e:
            return f"Error navegando {url} con Playwright: {e}"
