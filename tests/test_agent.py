"""Tests básicos de Archon."""
from unittest.mock import MagicMock, patch
from adv_archon.core.agent import Agent
from adv_archon.core.consent import ConsentGate
from adv_archon.core.memory import Memory
from adv_archon.plugins.loader import PluginLoader
from adv_archon.tools.files import FilesTool
from adv_archon.tools.mac_apps import MacAppsTool


def _make_agent(llm_response: str = "Hola") -> Agent:
    llm = MagicMock()
    llm.chat.return_value = llm_response

    memory = MagicMock(spec=Memory)
    memory.files_indexed.return_value = 0
    memory.search.return_value = []

    return Agent(
        llm=llm,
        files=FilesTool(),
        mac=MacAppsTool(),
        memory=memory,
        consent=ConsentGate(),
        plugins=PluginLoader(),
    )


def test_agent_creation():
    agent = _make_agent()
    assert agent is not None


def test_agent_process_returns_string():
    agent = _make_agent("¡Buenos días!")
    result = agent.process("Hola")
    assert isinstance(result, str)
    assert result == "¡Buenos días!"


def test_agent_tool_call_extraction():
    tool_response = '```tool\n{"tool": "list_dir", "params": {"path": "~"}}\n```'
    agent = _make_agent()
    parsed = agent._extract_tool_call(tool_response)
    assert parsed is not None
    assert parsed["tool"] == "list_dir"


def test_agent_reset_clears_history():
    agent = _make_agent("ok")
    agent.process("algo")
    assert len(agent._history) > 0
    agent.reset()
    assert len(agent._history) == 0


def test_consent_gate_deny():
    consent = ConsentGate()
    consent.deny_all = True
    result = consent.request("test_action", "Test")
    assert result is False


def test_plugin_loader_empty():
    loader = PluginLoader()
    assert loader.plugins == {}
    found, _ = loader.execute_by_action("no_existe")
    assert found is False
