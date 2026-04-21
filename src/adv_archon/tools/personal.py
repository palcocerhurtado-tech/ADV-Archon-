"""Personal connectors"""
class PersonalTool:
    def __init__(self):
        self.memory = {}
    
    def remember(self, key: str, value: str):
        self.memory[key] = value
    
    def recall(self, key: str):
        return self.memory.get(key)
