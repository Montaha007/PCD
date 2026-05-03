"""
orchestrator.py — Maps domain to agent (Numa-backed).

Usage:
    from ai.agents.orchestrator import get_agent
    agent = get_agent("wellness")
    result = agent.run(user_data)
"""
from __future__ import annotations

from .adapters import NumaAdapter, SleepAgentWithReasoning

_REGISTRY = {
    "wellness":        lambda: NumaAdapter(mode="full"),
    "sleep":           SleepAgentWithReasoning,
    "sleep_reasoning": lambda: NumaAdapter(mode="sleep_only"),
}


def get_agent(domain: str):
    """Return an agent instance for *domain*."""
    if domain not in _REGISTRY:
        available = ", ".join(_REGISTRY.keys())
        raise ValueError(f"No agent for '{domain}'. Available: {available}")
    factory = _REGISTRY[domain]
    return factory() if callable(factory) else factory()
