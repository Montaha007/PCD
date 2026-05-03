"""
adapters.py — Connects Django models to Numa agents.
Converts payloads, runs agents, returns structured recommendations.
"""
from __future__ import annotations
from typing import Any

from .base import BaseAgent
from .numa.main import analyze_user as numa_analyze_user


class NumaAdapter(BaseAgent):
    """Runs Numa's full multi-agent reasoning pipeline."""

    def __init__(self, mode: str = "full"):
        self.mode = mode

    def run(self, payload: Any) -> dict:
        user_data = self._format_payload(payload)
        try:
            result = numa_analyze_user(user_data)
            return {"success": True, "data": result, "mode": self.mode}
        except Exception as e:
            return {"success": False, "error": str(e), "mode": self.mode}

    def _format_payload(self, payload: Any) -> dict:
        if isinstance(payload, dict):
            return payload
        if hasattr(payload, "to_dict"):
            return payload.to_dict()
        return {
            "user_id": str(getattr(payload, "user_id", "unknown")),
            "sleep_features": getattr(payload, "sleep_features", {}),
            "lifestyle_features": getattr(payload, "lifestyle_features", {}),
            "journal_text": getattr(payload, "journal_text", ""),
        }


class SleepAgentWithReasoning(BaseAgent):
    """Sleep analysis backed by the full Numa reasoning pipeline."""

    def run(self, sleep_log) -> dict:
        duration_hours = sleep_log.calculated_sleep_duration.total_seconds() / 3600
        user_data = {
            "user_id": str(sleep_log.user.id),
            "sleep_features": {
                "Total_sleep_time(hour)": duration_hours,
                "Satisfaction_of_sleep": int(sleep_log.satisfaction_of_sleep),
                "Late_night_sleep": int(sleep_log.late_night_sleep),
                "Wakeup_frequently_during_sleep": int(sleep_log.wake_up_frequently),
                "Sleep_at_daytime": int(sleep_log.sleep_at_daytime),
                "Drowsiness_tiredness": int(sleep_log.drowsiness_tiredness),
                "Duration_of_this_problems(years)": int(sleep_log.duration_of_problems),
                "Recent_psychological_attack": int(sleep_log.recent_psychological_attack),
                "Afraid_of_getting_asleep": int(sleep_log.afraid_of_sleeping),
            },
            "lifestyle_features": {},
            "journal_text": "",
        }
        return NumaAdapter(mode="sleep_only").run(user_data)
