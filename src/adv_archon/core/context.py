"""Context management"""
class Context:
    def __init__(self):
        self.state = {}
    
    def set(self, key: str, value):
        self.state[key] = value
    
    def get(self, key: str, default=None):
        return self.state.get(key, default)
