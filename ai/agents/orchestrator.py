"""
Orchestrator — maps a domain string to the right agent instance.

Usage:
    from ai.agents.orchestrator import get_agent
    agent = get_agent("sleep")
    result = agent.run(sleep_log)
"""
from __future__ import annotations

from .sleep_agent import SleepAgent

_REGISTRY = {
    "sleep": SleepAgent,
}


def get_agent(domain: str):
    """Return a (cached, stateless) agent for *domain*."""
    if domain not in _REGISTRY:
        raise ValueError(f"No agent registered for domain '{domain}'.")
    return _REGISTRY[domain]()
