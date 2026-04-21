"""Configuration"""
import os

class Config:
    def __init__(self):
        self.api_key = os.getenv('ANTHROPIC_API_KEY', '')
        self.model = os.getenv('MODEL', 'claude-3-5-sonnet')
