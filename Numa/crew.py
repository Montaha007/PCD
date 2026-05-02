"""
crew.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.4   — Agent Orchestration with CrewAI
         §5.4.1 — Integration Overview
         §5.4.2 — Workflow Management and Execution Order
         §5.4.3 — Data Flow Between Agents

         §5.5   — Final System Output (returned by run_pipeline)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from crewai import Crew

from agents import (
    build_correlation_agent,    # §5.3.1
    build_reasoning_agent,      # §5.3.2
    build_recommendation_agent, # §5.3.3
)
from tasks import (
    build_correlation_task,     # §5.4.2 Task 1
    build_reasoning_task,       # §5.4.2 Task 2
    build_recommendation_task,  # §5.4.2 Task 3
)
from config import CREW_VERBOSE

logger = logging.getLogger(__name__)


# ══════════════════════════════════════════════════════════════════════════════
# §5.4.1  INTEGRATION OVERVIEW
#
# Three-agent pipeline orchestrated by CrewAI Process.sequential.
#
# §5.4.2 Execution order (strictly enforced):
#   Task 1: Correlation Agent  (§5.3.1) — aggregates §5.2 model outputs
#   Task 2: Reasoning Agent    (§5.3.2) — applies rules, ranks causes
#   Task 3: Recommendation Agent (§5.3.3) — generates §5.5 final output
#
# §5.4.3 Data flow between agents:
#   Model Layer (§5.2) ──► Task 1 description (injected as JSON string)
#   Task 1 output       ──► Task 2 via context=[correlation_task]
#   Task 2 output       ──► Task 3 via context=[reasoning_task]
#   Task 3 output       ──► §5.5 Final System Output (returned to caller)
#
# Architecture references:
#   §5.1.3.1 Qdrant  — used in sleep_inference + nlp_inference (§5.2)
#   §5.1.3.2 Neo4j   — used in nlp_inference (§5.2.3); evidence in §5.3.2.2
#   §5.1.3.3 LLM     — powers all three CrewAI agents (§5.3)
# ══════════════════════════════════════════════════════════════════════════════


# ─────────────────────────────────────────────────────────────────────────────
# §5.4.3  DATA FLOW — JSON parsing helpers
# ─────────────────────────────────────────────────────────────────────────────

def _parse_json(raw: str, stage: str) -> dict:
    """Strip LLM markdown artefacts and parse JSON output."""
    cleaned = raw.strip()

    # Strip code fences: ```json ... ``` or ``` ... ```
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()

    # Some LLMs embed the JSON inside a larger text — extract first {...} block
    if not cleaned.startswith("{"):
        start = cleaned.find("{")
        end   = cleaned.rfind("}")
        if start != -1 and end != -1 and end > start:
            cleaned = cleaned[start:end + 1]

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        logger.error("[%s] Invalid JSON — first 500 chars:\n%s", stage, raw[:500])
        raise ValueError(f"[{stage}] JSON parse error: {exc.msg}") from exc

    # If the LLM returned a JSON array, unwrap the first dict element
    if isinstance(parsed, list):
        for item in parsed:
            if isinstance(item, dict):
                return item
        raise ValueError(f"[{stage}] Expected a JSON object, got a list with no dict items")

    return parsed


def _validate(output: dict, required_keys: set, stage: str) -> None:
    """Light schema check — log warnings for missing keys."""
    missing = required_keys - output.keys()
    if missing:
        logger.warning("[%s] Missing keys: %s", stage, missing)


# ─────────────────────────────────────────────────────────────────────────────
# §5.4.2  CREW FACTORY — assembles the three-agent sequential crew
# ─────────────────────────────────────────────────────────────────────────────

def build_crew(model_outputs: dict) -> "Crew":
    """
    §5.4.1 / §5.4.2 — Assembles the CrewAI crew.

    Parameters
    ----------
    model_outputs : dict  —  from model_loader.run_all_models(user_data)
                    Keys: sleep_model, lifestyle_model, nlp_mental_health_model
    """
    try:
        from crewai import Crew, Process
    except Exception as exc:
        raise RuntimeError(
            "CrewAI is unavailable in the current Python environment. "
            "Use a compatible interpreter (e.g. .venv312)."
        ) from exc

    # §5.3.1 / §5.3.2 / §5.3.3 — agents
    corr_agent = build_correlation_agent()
    reas_agent = build_reasoning_agent()
    reco_agent = build_recommendation_agent()

    # §5.4.2 — tasks in execution order
    corr_task = build_correlation_task(corr_agent, model_outputs)  # Task 1
    reas_task = build_reasoning_task(reas_agent, corr_task)        # Task 2
    reco_task = build_recommendation_task(reco_agent, reas_task)   # Task 3

    crew = Crew(
        agents=[corr_agent, reas_agent, reco_agent],
        tasks=[corr_task, reas_task, reco_task],
        process=Process.sequential,   # §5.4.2 strict order
        verbose=CREW_VERBOSE,
        max_rpm=1,
    )
    logger.info("§5.4.1 Crew assembled: 3 agents, 3 tasks, process=sequential")
    return crew


# ─────────────────────────────────────────────────────────────────────────────
# §5.4.2  PIPELINE EXECUTION  +  §5.4.3  DATA FLOW EXTRACTION
# ─────────────────────────────────────────────────────────────────────────────

def run_pipeline(model_outputs: dict) -> dict[str, Any]:
    """
    §5.4 — Builds, executes, and returns the full three-agent pipeline.

    §5.4.3 Data flow:
      1. model_outputs injected into Task 1 description.
      2. Task 1 output → Task 2 context (CrewAI automatic injection).
      3. Task 2 output → Task 3 context (CrewAI automatic injection).
      4. Task 3 output = §5.5 Final System Output.

    Returns
    -------
    dict:
      unified_profile     — §5.3.1.4  (Correlation Agent output)
      reasoning_report    — §5.3.2.3  (Reasoning Agent output)
      final_output        — §5.5      (Recommendation Agent — FINAL)
      pipeline_metadata   — §5.4 execution summary
    """
    t0     = time.perf_counter()
    run_ts = datetime.now(timezone.utc).isoformat()
    logger.info("§5.4.2 Pipeline start — %s", run_ts)

    crew        = build_crew(model_outputs)
    crew_result = crew.kickoff()
    elapsed     = time.perf_counter() - t0
    logger.info("§5.4.2 Pipeline complete — %.2fs", elapsed)

    # §5.4.3 — Extract per-task raw strings
    tasks_output = getattr(crew_result, "tasks_output", [])

    def _get_raw(i: int) -> str:
        if tasks_output and len(tasks_output) > i:
            t = tasks_output[i]
            return t.raw if hasattr(t, "raw") else str(t)
        return "{}"

    raw_final: str = (
        crew_result.raw if hasattr(crew_result, "raw") else str(crew_result)
    )

    # §5.4.3 — Parse + validate each agent output
    unified_profile = _parse_json(_get_raw(0), "§5.3.1 Correlation")
    _validate(unified_profile,
              {"insomnia_detected", "overall_confidence", "aggregated_signals"},
              "§5.3.1")

    reasoning_report = _parse_json(_get_raw(1), "§5.3.2 Reasoning")
    _validate(reasoning_report,
              {"root_causes", "insomnia_confirmed", "referral_required"},
              "§5.3.2")

    final_output = _parse_json(raw_final, "§5.5 Final Output")
    _validate(final_output,
              {"diagnosis", "action_plan", "plan_summary"},
              "§5.5")

    # Log summary — defensive access in case LLM returns unexpected shapes
    causes     = reasoning_report.get("root_causes", [])
    if not isinstance(causes, list):
        causes = []
    primary    = next((c for c in causes if isinstance(c, dict) and c.get("rank") == "PRIMARY"), {})
    action_plan = final_output.get("action_plan", {})
    if not isinstance(action_plan, dict):
        action_plan = {}
    actions    = action_plan.get("short_term", {})
    if not isinstance(actions, dict):
        actions = {}
    actions    = actions.get("actions", [])

    logger.info(
        "§5.4.3 Data flow summary:\n"
        "  [§5.3.1] Profile  : insomnia=%s  conf=%.2f  tier=%s\n"
        "  [§5.3.2] Reasoning: confirmed=%s  primary='%s'  causes=%d  referral=%s\n"
        "  [§5.5  ] Output   : actions=%d  plan_conf=%.2f",
        unified_profile.get("insomnia_detected"),
        unified_profile.get("overall_confidence", 0),
        unified_profile.get("confidence_tier"),
        reasoning_report.get("insomnia_confirmed"),
        primary.get("cause", "—")[:40],
        len(causes),
        reasoning_report.get("referral_required"),
        len(actions),
        final_output.get("plan_confidence", 0),
    )

    return {
        "unified_profile":  unified_profile,   # §5.3.1.4
        "reasoning_report": reasoning_report,  # §5.3.2.3
        "final_output":     final_output,      # §5.5
        "pipeline_metadata": {
            "run_timestamp":     run_ts,
            "execution_seconds": round(elapsed, 2),
            "framework":         "CrewAI",
            "process":           "sequential",
            "sections":          ["§5.2","§5.3","§5.4","§5.5"],
            "agents":            3,
            "tasks":             3,
            "insomnia_confirmed":  reasoning_report.get("insomnia_confirmed"),
            "referral_required":   final_output.get("referral_required"),
            "confidence_tier":     unified_profile.get("confidence_tier"),
            "root_cause_count":    len(causes),
            "short_term_actions":  len(actions),
        },
    }
