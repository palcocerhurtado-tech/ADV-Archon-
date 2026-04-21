"""Google Gemini integration"""
class GeminiClient:
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    async def generate(self, prompt: str) -> str:
        return "Gemini response"
