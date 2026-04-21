"""File operations"""
import os

class FilesTool:
    def __init__(self):
        self.name = "files"
    
    def read(self, path: str) -> str:
        with open(path, 'r') as f:
            return f.read()
    
    def write(self, path: str, content: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
