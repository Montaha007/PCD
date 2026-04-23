"""
SleepAgent — thin wrapper around run_sleep_pipeline.

All prediction logic lives in ai/pipeline.py.
"""
from __future__ import annotations

from ..pipeline import run_sleep_pipeline
from .base import BaseAgent


class SleepAgent(BaseAgent):

    def run(self, sleep_log) -> dict:
        return run_sleep_pipeline(sleep_log)
