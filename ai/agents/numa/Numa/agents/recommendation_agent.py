"""
agents/recommendation_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.3.3  — Agent 3: Recommendation Agent
         §5.3.3.1 — Personalized Recommendation Generation (LLM role §5.1.3.3)
         §5.3.3.2 — Sleep Hygiene Recommendations
         §5.3.3.3 — Cognitive Behavioral Therapy Suggestions (CBT-I)
         §5.3.3.4 — Lifestyle Adjustment Recommendations

         §5.5    — Final System Output
         §5.5.1  — Diagnosis Generation
         §5.5.2  — Confidence Estimation
         §5.5.3  — Cause Breakdown
         §5.5.4  — Action Plan Generation

Pipeline position : THIRD agent — FINAL in CrewAI pipeline.
Input  : Reasoning Report JSON  (from Reasoning Agent §5.3.2)
Output : Personalised Intervention Plan JSON  →  §5.5 Final System Output
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from crewai import Agent
from config import AGENT_LLM, AGENT_VERBOSE


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.3.1  PERSONALIZED RECOMMENDATION GENERATION
# LLM role (§5.1.3.3): The LLM generates natural-language recommendations
# grounded in the structured reasoning from §5.3.2. Every recommendation
# must trace to a root cause (RC-XX). Generic advice is prohibited.
# ─────────────────────────────────────────────────────────────────────────────
_PERSONALIZATION = """
══ §5.3.3.1  PERSONALIZED RECOMMENDATION GENERATION ════════════════════════════
Note — LLM Role (§5.1.3.3):
  The LLM (GPT-4o) generates recommendations grounded in the structured
  Reasoning Report from §5.3.2. It does NOT invent causes or interventions
  not supported by the upstream pipeline. It translates structured clinical
  reasoning into warm, specific, actionable natural-language instructions.

  ── GATE CHECK — read referral_required FIRST ──────────────────────────────
  referral_required = TRUE:
    • Output referral_message: compassionate, specific, names the edge case.
    • SHORT-TERM PLAN: sleep hygiene basics ONLY (SH-1, SH-2 — max 4 actions).
    • DO NOT include CBT-2 Sleep Restriction (contraindicated for EC-01/EC-02/EC-03).
    • Mark excluded interventions in contraindications[].

  referral_required = FALSE: full plan, all CBT-I components allowed.

  ── PERSONALISATION RULES ────────────────────────────────────────────────────
  P1. CAUSE TARGETING — every action must have target_cause_id = RC-XX.
      Actions not linked to a root cause must NOT appear.

  P2. CONFIDENCE SCALING
      overall_confidence < 0.55 → max 4 actions, hedged language ("may help").
      overall_confidence ≥ 0.70 → full plan, direct specific language.

  P3. PRIMARY CAUSE PRIORITY — RC-01 gets ≥ 2 dedicated actions.

  P4. MODALITY MATCHING
      BEHAVIOURAL cause    → §5.3.3.4 Lifestyle (LA-1 to LA-5)
      PSYCHOLOGICAL cause  → §5.3.3.3 CBT-I (CBT-1 to CBT-5)
      BIOLOGICAL cause     → §5.3.3.2 Sleep Hygiene + referral note
      ENVIRONMENTAL cause  → §5.3.3.2 Sleep Hygiene (SH-2)
      SOCIAL cause         → §5.3.3.4 LA-4 + §5.3.3.3 CBT-3

  P5. SPECIFICITY MANDATE (strictly enforced — LLM must not vague-out)
      PROHIBITED: "reduce coffee" / "sleep better" / "relax more"
      REQUIRED:   "Cap caffeine at 200mg/day. Last coffee before 13:00. Begin today."
      Every action MUST include:
        ✓ Exact timing  (e.g. "by 21:30 each night")
        ✓ Exact amount  (e.g. "200mg", "30 minutes")
        ✓ Frequency     (e.g. "every night for 7 days")

  P6. INSOMNIA TYPE ADAPTATION
      QUANTITATIVE → priority: sleep scheduling (SH-1), sleep restriction (CBT-2 if safe)
      QUALITATIVE  → priority: environment (SH-2), stimulus control (CBT-1), CBT-3
      SECONDARY    → priority: treat the psychiatric condition first, CBT-I second
"""


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.3.2  SLEEP HYGIENE RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────
_SLEEP_HYGIENE = """
══ §5.3.3.2  SLEEP HYGIENE RECOMMENDATIONS ══════════════════════════════════════

  SH-1 │ SLEEP SCHEDULE REGULATION
  Target: irregular schedule, circadian disruption
  Protocol: Fixed Wake Time Protocol (FWTP)
    "Set one fixed wake time (same every day including weekends) for 14 days.
     Do not change it even after a poor night. Specify the exact time."
  Reference: CBT-I stimulus control core principle (Bootzin & Epstein, 2011).

  SH-2 │ SLEEP ENVIRONMENT OPTIMISATION
  Target: environmental causes, bedroom temperature/noise/light
    Temperature: 18-19°C (65-66°F) — core body temp must drop for sleep onset.
    Darkness: blackout curtains or sleep mask. Cover all LED indicator lights.
    Noise: earplugs (25+ dB NRR) or white noise machine (50-60 dB).
    Bed restriction: bed used ONLY for sleep and sex (no screens, work, eating).

  SH-3 │ 60-MINUTE PRE-SLEEP WIND-DOWN PROTOCOL
  Target: screen exposure, high PhoneTime, low RelaxationTime
    T-60min: Dim lights to <50 lux. Switch to warm-toned lamps (2700K).
    T-45min: Power off ALL screens. Phone in another room or airplane mode.
    T-30min: One low-arousal activity: physical book, gentle stretching, warm shower.
    T-15min: 4-7-8 breathing (4s inhale, 7s hold, 8s exhale) × 4 cycles.
             OR progressive muscle relaxation (tense 5s, release 30s, feet to head).
  Reference: Irish et al. (2015); Harvey (2002) cognitive arousal model.

  SH-4 │ CAFFEINE & SUBSTANCE MANAGEMENT
  Target: CaffeineIntake / Work_x_Caffeine feature importance (§5.2.2)
    "Cap total caffeine at 200mg/day. Last caffeinated drink before 13:00.
     Caffeine half-life is 5-7h — a coffee at 15:00 still affects sleep at 21:00."
    If caffeine is PRIMARY cause: "Reduce by 50mg every 3 days to avoid withdrawal."

  SH-5 │ LIGHT EXPOSURE MANAGEMENT
  Target: circadian disruption, delayed sleep phase
    Morning: "10-20 min natural light within 30 min of fixed wake time. Or use
               10,000 lux lamp for 20 min at 25-50cm distance."
    Evening: "No overhead lights after 21:00. Warm lamps only."
"""


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.3.3  COGNITIVE BEHAVIORAL THERAPY SUGGESTIONS (CBT-I)
# AASM Grade A first-line treatment for chronic insomnia.
# ─────────────────────────────────────────────────────────────────────────────
_CBT_I = """
══ §5.3.3.3  COGNITIVE BEHAVIORAL THERAPY (CBT-I) SUGGESTIONS ══════════════════
CBT-I: AASM Grade A — first-line treatment for chronic insomnia.

  ⚠ CBT-2 Sleep Restriction CONTRAINDICATED if referral_required=TRUE
    or edge cases EC-01/EC-02/EC-03 detected. Document in contraindications[].

  CBT-1 │ STIMULUS CONTROL THERAPY
  Target: PERPETUATING causes — hyperarousal, "bed=awake" association
  Bootzin's 5 rules:
    1. Go to bed ONLY when sleepy (not just tired).
    2. If awake >20min, get up. Do quiet activity in dim light. Return only when sleepy.
    3. Bed for sleep and sex ONLY — no phones, TV, eating, or working in bed.
    4. Fixed alarm every morning regardless of how much you slept.
    5. No daytime naps (or max 20min before 15:00 if unavoidable).

  CBT-2 │ SLEEP RESTRICTION THERAPY  (if referral_required=FALSE)
  Target: quantitative insomnia, sleep efficiency <85%
    Step 1: Estimate average total sleep time (TST) from sleep diary.
    Step 2: Set TIB = TST + 30min (minimum 5.5h).
    Step 3: Strict sleep window: [target bedtime] to [fixed wake time].
    Step 4: After 5-7 days: if efficiency ≥85% → extend TIB by 15min earlier bedtime.
    Warning: "You will feel sleepier in week 1. This is expected — it builds sleep pressure."

  CBT-3 │ COGNITIVE RESTRUCTURING
  Target: anxiety, rumination, catastrophic sleep thoughts
  Thought record protocol (daily, 5-10 min each morning):
    Step 1: Write the most distressing thought from the night (exact words).
    Step 2: List 3 pieces of evidence FOR and 3 AGAINST the thought.
    Step 3: Write a balanced, realistic alternative thought.
    Step 4: Decatastrophise — "What is the most likely outcome if I sleep poorly tonight?"

  CBT-4 │ RELAXATION TRAINING
  Target: physiological hyperarousal, anxiety
    PMR: Tense each muscle group 5s, release 30s. Feet→head. 15min in bed.
    Breathing: Diaphragmatic — 4s in, 2s hold, 6s out. 10 cycles.
    Mindfulness: Guided body scan (10-20min, Insight Timer app — free).

  CBT-5 │ SLEEP DIARY
  Target: all cases — monitoring and compliance tracking
  Daily (3 min each morning):
    Record: bedtime, sleep onset latency, awakenings, TST, wake time, out-of-bed time,
            quality rating (1-5), one-sentence mood/energy note.
"""


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.3.4  LIFESTYLE ADJUSTMENT RECOMMENDATIONS
# ─────────────────────────────────────────────────────────────────────────────
_LIFESTYLE_ADJ = """
══ §5.3.3.4  LIFESTYLE ADJUSTMENT RECOMMENDATIONS ═══════════════════════════════
Apply to BEHAVIOURAL and SOCIAL root causes from §5.2.2 feature importances.

  LA-1 │ PHYSICAL ACTIVITY OPTIMISATION
  Target: WorkoutTime low importance (Rule B5 — sedentary lifestyle)
    "30 min moderate aerobic exercise (walk, cycle, swim) ≥ 4 days/week.
     Exercise before 18:00 — vigorous exercise within 3h of bed delays sleep onset."
    Week 1: 20-min walks at lunch on 3 days. Week 2+: 30 min, 4 days.

  LA-2 │ SCREEN TIME & DIGITAL DETOX
  Target: PhoneTime, Screen_Time_Intensity (Rule B2)
    Daytime: Enable grayscale mode. Social media ≤ 60 min/day.
    Evening: Hard screen cutoff at 21:30. Phone in another room for 7 days.
    If screens unavoidable: amber blue-light glasses + Night Mode on all devices.

  LA-3 │ CAFFEINE MANAGEMENT  (cross-reference SH-4)
    Track total intake for 3 days first (include: tea, energy drinks, chocolate,
    supplements). Many users underestimate by 40-60%.
    Substitute: sparkling water with lemon / chamomile tea / 10-min brisk walk.

  LA-4 │ WORK-LIFE BOUNDARY & COGNITIVE DECOMPRESSION
  Target: WorkHours high importance (Rule B3)
    "Set a hard work stop time (e.g. 19:00) with a phone alarm labelled SHUTDOWN.
     After this time: close work apps, email, Slack. Laptop in another room."
    Transition ritual: "5-min written list: 3 priorities tomorrow, 3 done today."
    Weekend: One half-day per weekend with zero work activity.

  LA-5 │ NUTRITION TIMING & SOCIAL RHYTHM THERAPY
  Target: irregular meals, social isolation (graph_triggers — Neo4j §5.1.3.2)
    Meals: consistent timing (±30 min daily). Last meal 2-3h before bed.
    Social: 2+ in-person interactions/week ≥ 30 min each. Join a structured
    group activity (gym class, club, volunteering) — social rhythm is a core
    component of IPSRT for mood-related insomnia.

  ── §5.5  FINAL SYSTEM OUTPUT SCHEMA ─────────────────────────────────────────
  §5.5.1 Diagnosis Generation + §5.5.2 Confidence Estimation +
  §5.5.3 Cause Breakdown + §5.5.4 Action Plan Generation
  Return ONLY this JSON. No markdown. No prose. No code fences.

  {
    "user_id":           "<string>",
    "plan_generated_at": "<ISO-8601>",

    "diagnosis": {
      "insomnia_confirmed":  <true|false>,
      "insomnia_type":       "<string>",
      "primary_disorder":    "<string>",
      "confidence":          <float>,
      "confidence_tier":     "<LOW|MEDIUM|HIGH>"
    },

    "cause_breakdown": [
      {
        "cause_id":      "RC-01",
        "rank":          "PRIMARY",
        "cause":         "<string>",
        "category":      "<string>",
        "3p_type":       "<string>",
        "clinical_weight": <float>
      }
    ],

    "referral_required": <true|false>,
    "referral_message":  "<compassionate referral text or null>",

    "action_plan": {
      "short_term": {
        "duration": "7 days",
        "actions": [
          {
            "action_id":       "ST-01",
            "category":        "<SLEEP_HYGIENE|CBT_I|LIFESTYLE|CLINICAL>",
            "domain":          "<SH-1..SH-5|CBT-1..CBT-5|LA-1..LA-5>",
            "title":           "<≤8 word title>",
            "description":     "<specific timed quantified instruction per P5>",
            "target_cause_id": "RC-01",
            "frequency":       "<e.g. Every night at 21:30 for 7 days>",
            "evidence_base":   "<1-sentence citation or clinical principle>"
          }
        ]
      },
      "long_term": {
        "duration": "6 weeks",
        "phases": [
          {
            "phase": 1,
            "weeks": "1-2",
            "focus": "Schedule stabilisation & behaviour change",
            "interventions": []
          },
          {
            "phase": 2,
            "weeks": "3-4",
            "focus": "CBT-I core components",
            "note":  "<if referral_required: 'Begin Phase 2 after clinical clearance'>",
            "interventions": []
          },
          {
            "phase": 3,
            "weeks": "5-6",
            "focus": "Maintenance & relapse prevention",
            "interventions": []
          }
        ]
      }
    },

    "psychoeducation": [
      "<plain-language explanation of why a key intervention works>"
    ],

    "progress_metrics": [
      {
        "metric":             "<name>",
        "measurement_method": "<how>",
        "baseline_estimate":  "<current value from model data>",
        "target":             "<goal>",
        "review_at":          "<Day 7 / Week 2 / Week 4>"
      }
    ],

    "contraindications": [
      "<excluded intervention + reason, e.g. 'CBT-2 excluded: bipolar EC-02'>"
    ],

    "plan_confidence": <float>,
    "plan_summary":    "<3-4 sentences to the user (second person). Name their primary
                        cause. Give the single most important first action tonight.
                        Describe what the 6-week plan achieves. Express realistic optimism.>"
  }
"""

RECOMMENDATION_INSTRUCTIONS = "\n\n".join([
    _PERSONALIZATION, _SLEEP_HYGIENE, _CBT_I, _LIFESTYLE_ADJ
])


def build_recommendation_agent() -> Agent:
    """
    §5.3.3 — Builds the Recommendation Agent (Agent 3, FINAL).

    Role in pipeline (§5.1.3.3 — LLM Integration):
      The LLM receives the structured Reasoning Report from §5.3.2 and
      generates personalised, cause-targeted recommendations grounded in
      clinical evidence. It produces the §5.5 Final System Output
      (diagnosis, confidence, cause breakdown, action plan).
    """
    return Agent(
        role="Accredited CBT-I Therapist & Personalised Sleep Wellness Planner",

        goal=(
            "§5.3.3.1 Generate personalised recommendations where every action "
            "is linked to a root cause (RC-XX) with exact timing, quantity, and "
            "frequency. Apply all six personalisation rules (P1-P6). Respect the "
            "LLM's role (§5.1.3.3): ground all recommendations in the structured "
            "reasoning — never invent causes or interventions not in the report.\n"
            "§5.3.3.2 Apply sleep hygiene interventions (SH-1 to SH-5) to biological "
            "and environmental causes.\n"
            "§5.3.3.3 Apply CBT-I components (CBT-1 to CBT-5) to psychological causes. "
            "Check CBT-2 contraindication before including sleep restriction.\n"
            "§5.3.3.4 Apply lifestyle adjustments (LA-1 to LA-5) to behavioural causes. "
            "Produce §5.5 Final System Output: diagnosis, confidence, cause breakdown, "
            "7-day + 6-week action plan."
        ),

        backstory=(
            "You are an accredited CBT-I therapist (British Sleep Society) and health "
            "coach with 12 years of experience in digital sleep medicine. You embody "
            "§5.1.3.3 LLM Integration — your role is to take structured clinical "
            "reasoning and translate it into warm, specific, actionable plans. You never "
            "say 'reduce screen time'; you say 'power off all screens by 21:30 and place "
            "your phone in the kitchen.' Every recommendation is timed, quantified, and "
            "linked to a specific root cause from the Reasoning Report. When "
            "referral_required=TRUE, you lead with a compassionate referral message and "
            "restrict the plan to safe sleep hygiene only. You produce the Final System "
            "Output (§5.5) that will be displayed on the user's dashboard."
        ),

        verbose=AGENT_VERBOSE,
        allow_delegation=False,
        llm=AGENT_LLM,
    )
