"""
tasks/recommendation_task.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.4.2 — Workflow Management: Task 3 of 3 (FINAL)
         §5.4.3 — Data Flow: Reasoning Agent → Recommendation Agent → §5.5 Output
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from crewai import Task, Agent


def build_recommendation_task(agent: Agent, reasoning_task: Task) -> Task:
    """
    §5.4.2 — Task 3 (FINAL in sequential pipeline).
    §5.4.3 — Data flow: Reasoning Report → Recommendation Agent → §5.5 Output.
    """
    description = """TASK 3/3 — RECOMMENDATION AGENT §5.3.3 (FINAL)
The Reasoning Report from Task 2 is in your context.

Produce the §5.5 Final System Output applying §5.3.3.1–§5.3.3.4 (as defined in your role):
- Check referral gate first. If referral_required: include referral_message + SH-1/SH-2 only.
- Otherwise: personalisation (P1-P6), sleep hygiene (SH-1–SH-5), CBT-I (CBT-1–CBT-5),
  lifestyle actions (LA-1–LA-5), 6-week phased plan, psychoeducation, progress metrics.
- Every action must have timing + quantity + frequency (specificity mandate P5).
- Output ONLY the §5.5 JSON. No markdown, no prose, no code fences.
- Every action must have a non-null target_cause_id (RC-XX)."""

    return Task(
        description=description,
        agent=agent,
        context=[reasoning_task],
        expected_output=(
            "Single valid JSON — §5.5 Final System Output. "
            "Keys: user_id, plan_generated_at, diagnosis, cause_breakdown, "
            "referral_required, referral_message, action_plan (short_term 7-day + "
            "long_term 3-phase), psychoeducation, progress_metrics, contraindications, "
            "plan_confidence, plan_summary."
        ),
    )
