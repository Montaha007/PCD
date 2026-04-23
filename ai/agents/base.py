"""Abstract base class for all domain agents."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    """
    Every agent receives raw input (e.g. a model instance or a dict)
    and returns a structured result dict.
    """

    @abstractmethod
    def run(self, payload: Any) -> dict:
        """Execute the agent and return its result."""
        ...
