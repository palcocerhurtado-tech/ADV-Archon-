"""LLM Client"""
class LLMClient:
    def __init__(self, model: str):
        self.model = model
    
    async def generate(self, prompt: str) -> str:
        return f"Response from {self.model}"
