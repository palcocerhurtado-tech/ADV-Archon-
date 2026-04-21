"""Text-to-Speech"""
class TTSClient:
    async def speak(self, text: str) -> str:
        return f"Speaking: {text}"
