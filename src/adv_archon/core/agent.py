"""ADV Archon Agent"""
from .context import Context
from .intent import Intent

class Agent:
    def __init__(self, config: dict):
        self.config = config
        self.context = Context()
    
    async def process(self, user_input: str) -> str:
        intent = Intent.parse(user_input)
        return f"Processing: {intent.action}"
