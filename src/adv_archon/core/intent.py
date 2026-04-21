"""Intent parsing"""
from dataclasses import dataclass

@dataclass
class Intent:
    action: str
    params: dict = None
    
    @staticmethod
    def parse(text: str):
        return Intent(action=text, params={})
