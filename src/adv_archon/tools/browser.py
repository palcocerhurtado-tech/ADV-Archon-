"""Browser automation"""
class BrowserTool:
    def __init__(self):
        self.name = "browser"
    
    async def navigate(self, url: str):
        return f"Navigating to {url}"
    
    async def extract_content(self, selector: str):
        return "Content extracted"
