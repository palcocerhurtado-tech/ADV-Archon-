"""Agent tests"""
from src.adv_archon.core.agent import Agent

def test_agent_creation():
    config = {'model': 'test'}
    agent = Agent(config)
    assert agent.config == config
