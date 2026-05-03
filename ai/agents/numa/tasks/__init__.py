"""tasks/ — §5.4 Agent Orchestration with CrewAI"""
from .correlation_task    import build_correlation_task    # §5.4.2 Task 1
from .reasoning_task      import build_reasoning_task      # §5.4.2 Task 2
from .recommendation_task import build_recommendation_task # §5.4.2 Task 3

__all__ = [
    "build_correlation_task",
    "build_reasoning_task",
    "build_recommendation_task",
]
