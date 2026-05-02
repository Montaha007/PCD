"""
tasks/reasoning_task.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.4.2 — Workflow Management: Task 2 of 3
         §5.4.3 — Data Flow: Correlation Agent → Reasoning Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from crewai import Task, Agent


def build_reasoning_task(agent: Agent, correlation_task: Task) -> Task:
    """
    §5.4.2 — Task 2 (SECOND in sequential pipeline).
    §5.4.3 — Data flow: Unified Profile JSON injected via context=[correlation_task].
    """
    description = """TASK 2/3 — REASONING AGENT §5.3.2
The Unified Insomnia Profile from Task 1 is in your context.

Apply §5.3.2.1–§5.3.2.3 (as defined in your role):
- Rule Sets A-D to confirm insomnia and identify root causes.
- Score and rank causes (RC-01 = PRIMARY). Max 6 causes.
- Screen all 8 edge cases. Set referral_required accordingly.
- Output ONLY the Reasoning Report JSON. No prose, no markdown, no code fences.
- root_causes[] sorted by clinical_weight DESC."""

    return Task(
        description=description,
        agent=agent,
        context=[correlation_task],
        expected_output=(
            "Single valid JSON — Reasoning Report (§5.3.2.3). "
            "Keys: user_id, reasoning_timestamp, insomnia_confirmed, insomnia_type, "
            "primary_disorder, rules_applied, root_causes (sorted DESC), edge_cases, "
            "reasoning_summary, referral_required, referral_reason, confidence_in_reasoning, data_gaps."
        ),
    )
