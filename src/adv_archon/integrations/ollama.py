"""Ollama local LLM"""
class OllamaClient:
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
    
    async def generate(self, prompt: str) -> str:
        return "Ollama response"
