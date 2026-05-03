"""
main.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Entry point — runs the full pipeline from §5.2 Model Layer through §5.5 Output.

Usage:
    python main.py                     # uses built-in sample data
    python main.py --user user-123     # custom user ID

Your backend colleague calls analyze_user(user_data) — that's the interface.
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import logging
from datetime import datetime, timezone
from .model_loader import run_all_models
from .crew import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


# ── Sample user data (replace with real frontend payload) ─────────────────────
SAMPLE_USER_DATA = {
    "user_id": "user-001",

    # §5.2.1 — Sleep log data (§3.1.1): hours, quality, patterns
   "sleep_features": {
        "Total_sleep_time(hour)": 5.2,
        "Satisfaction_of_sleep": 3,
        "Late_night_sleep": 1,
        "Wakeup_frequently_during_sleep": 1,
        "Sleep_at_daytime": 0,
        "Drowsiness_tiredness": 1,
        "Duration_of_this_problems(years)": 2,
        "Recent_psychological_attack": 1,
        "Afraid_of_getting_asleep": 1,
        },

    # §5.2.2 — Lifestyle log data (§3.1.2): routines, habits, diet
    "lifestyle_features": {
        "WorkoutTime":    0.5,    # hours/day
        "ReadingTime":    0.3,
        "PhoneTime":      4.2,    # hours/day — high screen time
        "WorkHours":      10.5,   # hours/day — overworked
        "CaffeineIntake": 380,    # mg/day — excessive
        "RelaxationTime": 0.4,    # hours/day — insufficient
    },

    # §5.2.3 — Journal entries (§3.1.3): free-text, daily logs
    "journal_text": (
        "I've been feeling really anxious lately. Every night my thoughts race "
        "and I keep worrying about work deadlines and whether I'll be able to "
        "perform well tomorrow. I lie in bed for hours unable to switch off. "
        "I'm exhausted but my mind won't stop. I feel completely drained during "
        "the day and I'm struggling to concentrate on anything. The pressure at "
        "work is overwhelming and I can't seem to find any time to relax."
    ),
}


def analyze_user(user_data: dict) -> dict:
    """
    Public interface for your backend colleague.

    Parameters
    ----------
    user_data : dict
        Must contain: user_id, sleep_features, lifestyle_features, journal_text

    Returns
    -------
    dict:
        unified_profile  — §5.3.1.4
        reasoning_report — §5.3.2.3
        final_output     — §5.5 (diagnosis + cause breakdown + action plan)
        pipeline_metadata
    """
    # §5.2 — Run all three models in real-time
    model_outputs = run_all_models(user_data)

    # §5.3 + §5.4 — Run the three-agent CrewAI pipeline
    result = run_pipeline(model_outputs)

    return result


def _print_section(title: str) -> None:
    print(f"\n{'═'*70}\n  {title}\n{'═'*70}")


def main():
    start = datetime.now(timezone.utc)
    logger.info("Pipeline starting...")

    result = analyze_user(SAMPLE_USER_DATA)

    elapsed = (datetime.now(timezone.utc) - start).total_seconds()
    logger.info("Pipeline completed in %.1fs", elapsed)

    # Print results
    _print_section("§5.3.1.4  UNIFIED INSOMNIA PROFILE  (Correlation Agent)")
    print(json.dumps(result["unified_profile"], indent=2, ensure_ascii=False))

    _print_section("§5.3.2.3  REASONING REPORT  (Reasoning Agent)")
    print(json.dumps(result["reasoning_report"], indent=2, ensure_ascii=False))

    _print_section("§5.5  FINAL SYSTEM OUTPUT  (Recommendation Agent)")
    print(json.dumps(result["final_output"], indent=2, ensure_ascii=False))

    _print_section("§5.4  PIPELINE METADATA")
    print(json.dumps(result["pipeline_metadata"], indent=2))

    # Save full output
    ts   = start.strftime("%Y%m%d_%H%M%S")
    path = f"output_{ts}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)
    logger.info("Full output saved to: %s", path)


if __name__ == "__main__":
    main()
