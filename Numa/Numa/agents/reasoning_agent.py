"""
agents/reasoning_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.3.2  — Agent 2: Reasoning Agent
         §5.3.2.1 — Rule-Based Reasoning  (3P Model + DSM-5 + ICSD-3)
         §5.3.2.2 — Root Cause Ranking    (includes Neo4j graph traversal §5.1.3.2)
         §5.3.2.3 — Edge Case Detection

Pipeline position : SECOND agent in CrewAI sequential pipeline.
Input  : Unified Insomnia Profile JSON  (from Correlation Agent §5.3.1)
Output : Structured Reasoning Report JSON  →  consumed by Recommendation Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from crewai import Agent
from config import AGENT_LLM, AGENT_VERBOSE


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.2.1  RULE-BASED REASONING
# 3P Model (Spielman 1987) + DSM-5 + ICSD-3 clinical rule sets.
# ─────────────────────────────────────────────────────────────────────────────
_RULE_BASED_REASONING = """
══ §5.3.2.1  RULE-BASED REASONING ══════════════════════════════════════════════

  ┌──────────────────────────────────────────────────────────────────────────┐
  │  CLINICAL FRAMEWORK: 3P MODEL (Spielman, 1987)                          │
  │  PREDISPOSING  — inherent vulnerabilities (traits, genetics, history)   │
  │  PRECIPITATING — acute triggers that started the problem                │
  │  PERPETUATING  — behaviours/cognitions that maintain the problem        │
  │  Frameworks: DSM-5 Insomnia Disorder + ICSD-3 Chronic/Short-Term       │
  └──────────────────────────────────────────────────────────────────────────┘

  RULE SET A — INSOMNIA CONFIRMATION
  ────────────────────────────────────────────────────────────────────────────
  A1. insomnia_detected=TRUE AND confidence_tier="HIGH"
      → CONFIRMED INSOMNIA. Proceed to full cause analysis (B, C, D).

  A2. insomnia_detected=TRUE AND confidence_tier="MEDIUM"
      → PROBABLE INSOMNIA. Proceed with uncertainty noted throughout.

  A3. insomnia_detected=FALSE AND dominant_mental_state ∈
      {depression, anxiety, stress, bipolar, suicidal}
      → PROBABLE SECONDARY INSOMNIA. Sleep disturbance is a symptom of the
        psychiatric condition. Flag: SECONDARY_INSOMNIA_SUSPECTED.

  A4. insomnia_detected=FALSE AND sleep_quality_label ∈ {INSUFFICIENT, BORDERLINE}
      AND confidence_tier="LOW"
      → INCONCLUSIVE. Flag: REQUIRES_CLINICAL_ASSESSMENT.

  A5. insomnia_type="QUALITATIVE" (from CONFLICT-2)
      → Focus analysis on sleep architecture disruption, not duration.

  RULE SET B — LIFESTYLE CAUSE RULES  (from §5.2.2 feature_importances)
  ────────────────────────────────────────────────────────────────────────────
  B1. "CaffeineIntake" OR "Work_x_Caffeine" ∈ top_3_features
      AND predicted_sleep_hours < 7.0
      → Cause: "Excessive caffeine disrupting sleep onset latency"
        3P: PRECIPITATING (recent) / PERPETUATING (chronic)  |  BEHAVIOURAL

  B2. "PhoneTime" OR "Screen_Time_Intensity" ∈ top_3_features
      → Cause: "Pre-sleep screen exposure — blue-light melatonin suppression"
        3P: PERPETUATING  |  BEHAVIOURAL

  B3. "WorkHours" ∈ top_3_features WITH positive importance
      → Cause: "Occupational overload — cognitive hyperarousal before sleep"
        3P: PRECIPITATING / PERPETUATING  |  SOCIAL/BEHAVIOURAL

  B4. "RelaxationTime" has NEGATIVE importance
      → Cause: "Insufficient pre-sleep wind-down routine"
        3P: PERPETUATING  |  BEHAVIOURAL

  B5. "WorkoutTime" has NEGATIVE importance
      → Cause: "Sedentary lifestyle reducing homeostatic sleep pressure"
        3P: PREDISPOSING  |  BEHAVIOURAL

  B6. sleep_quality_label="EXCESSIVE" AND predicted_sleep_hours > 9.0
      → Flag: HYPERSOMNIA_POSSIBLE. Cross-check with dominant_mental_state.
        If dominant_mental_state="depression": add Cause B6a (depression hypersomnia)
        3P: PREDISPOSING+PERPETUATING  |  PSYCHOLOGICAL

  B7. primary_cause from lifestyle model explicitly stated
      → Include it even if not captured by B1-B6.

  RULE SET C — PSYCHOLOGICAL CAUSE RULES  (from §5.2.3 NLP + Neo4j §5.1.3.2)
  ────────────────────────────────────────────────────────────────────────────
  C1. dominant_mental_state="anxiety"
      → Cause: "Cognitive hyperarousal and bedtime rumination"
        3P: PERPETUATING  |  PSYCHOLOGICAL  |  Modifiability: HIGH (CBT-I target)

  C2. dominant_mental_state="depression"
      → Cause: "Depressive episode with insomnia or early-morning awakening"
        3P: PREDISPOSING + PERPETUATING  |  PSYCHOLOGICAL  |  Bidirectional.

  C3. dominant_mental_state="stress"
      → Cause: "Acute stress — HPA axis activation, elevated evening cortisol"
        3P: PRECIPITATING  |  PSYCHOLOGICAL

  C4. dominant_mental_state="bipolar"
      → Cause: "Circadian disruption from bipolar mood cycles"
        3P: PREDISPOSING  |  BIOLOGICAL  |  Add EC-02. referral_required=TRUE.

  C5. dominant_mental_state="suicidal"
      → CRITICAL. referral_required=TRUE immediately. Add EC-01.
        Cause analysis is secondary to safety.

  C6. dominant_mental_state="personality disorder"
      → Cause: "Emotional dysregulation causing hyperarousal"
        3P: PREDISPOSING  |  PSYCHOLOGICAL  |  Add EC-05. referral_required=TRUE.

  C7. "insomnia" OR "fatigue" ∈ knowledge_graph.top_symptoms (Neo4j §5.1.3.2)
      → Confirms insomnia as documented in the knowledge graph.

  C8. graph_triggers (Neo4j) OR root_causes_extracted contains
      {work pressure, isolation, abandonment, financial stress, trauma}
      → Add PRECIPITATING cause for each trigger found.

  C9. secondary_emotions ∈ {hopelessness, emptiness, numbness}
      → Elevate depression signal by +0.10. Note in reasoning_summary.

  RULE SET D — CROSS-SIGNAL RULES
  ────────────────────────────────────────────────────────────────────────────
  D1. insomnia_type="QUALITATIVE" (from CONFLICT-2)
      → Cause: "Sleep architecture disruption (fragmented sleep, reduced N3/REM)"
        Evidence: conflict between classifer + regressor.  3P: PERPETUATING.
        Note: PSG or actigraphy needed for confirmation.

  D2. CONFLICT-5 detected (label mismatch, both >0.65)
      → Add causes for BOTH competing disorders. Flag: COMORBIDITY_POSSIBLE.

  D3. missing_signals non-empty
      → Reduce clinical_weight of causes from the missing model by 0.15.

  D4. CONFLICT-3 detected (BEHAVIOURAL_AETIOLOGY_SUSPECTED)
      → Force at least one BEHAVIOURAL cause as PRIMARY.
"""


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.2.2  ROOT CAUSE RANKING
# Three-criterion clinical weight score.
# Note: Neo4j graph traversal (§5.1.3.2) enriches the evidence field.
# ─────────────────────────────────────────────────────────────────────────────
_ROOT_CAUSE_RANKING = """
══ §5.3.2.2  ROOT CAUSE RANKING ════════════════════════════════════════════════
Note: The evidence field MUST reference Neo4j graph entities (§5.1.3.2) when
      graph_symptoms / graph_triggers / graph_emotions support the cause.

  clinical_weight = C1 + C2 + C3

  C1 — Model Convergence Score  [0.05 – 0.50]
    3 models converge  → +0.50
    2 models converge  → +0.30
    1 model only       → +0.10
    Implicit/derived   → +0.05

  C2 — Confidence Contribution  [0.00 – 0.30]
    convergence_conf = Σ w_model_norm (supporting models)
    contribution     = min(convergence_conf × 0.40, 0.30)

  C3 — Modifiability Score  [0.05 – 0.20]
    BEHAVIOURAL  (caffeine, screen, schedule, exercise) → +0.20
    PSYCHOLOGICAL (anxiety, rumination, stress)         → +0.15
    ENVIRONMENTAL (noise, light, temperature)           → +0.15
    SOCIAL        (work pressure, isolation)            → +0.10
    BIOLOGICAL    (genetics, circadian, comorbid)       → +0.05

  Rules:
    • Sort causes by clinical_weight DESC.
    • Highest = rank="PRIMARY" (RC-01). All others = rank="SECONDARY".
    • Tie-break: BEHAVIOURAL > PSYCHOLOGICAL > SOCIAL > BIOLOGICAL.
    • Maximum 6 causes. Merge closely related ones.
    • IDs: RC-01 (PRIMARY), RC-02 ... RC-06 (SECONDARY).

  Evidence field per cause:
    Cite: which models support it, specific field values, rule applied,
    AND any Neo4j graph entities (§5.1.3.2) that confirm the cause.
    Example: "CaffeineIntake importance=0.34, predicted_sleep_hours=5.8h,
              Neo4j: 'caffeine' linked to 'insomnia' via CAUSES (12 connections).
              Rule B1 applied."

  OUTPUT FORMAT per cause:
  {
    "cause_id":          "RC-01",
    "rank":              "PRIMARY",
    "cause":             "<concise label>",
    "category":          "<BEHAVIOURAL|PSYCHOLOGICAL|BIOLOGICAL|ENVIRONMENTAL|SOCIAL>",
    "3p_type":           "<PREDISPOSING|PRECIPITATING|PERPETUATING>",
    "supporting_models": ["lifestyle_model", "nlp_model"],
    "evidence":          "<field values + rule + Neo4j entities if applicable>",
    "clinical_weight":   <float>,
    "modifiability":     "<HIGH|MEDIUM|LOW>",
    "rule_applied":      "<e.g. Rule B1>"
  }
"""


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.2.3  EDGE CASE DETECTION + FINAL OUTPUT SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
_EDGE_CASE_DETECTION = """
══ §5.3.2.3  EDGE CASE DETECTION ════════════════════════════════════════════════
Screen ALL eight patterns. Check in order. referral_required=TRUE if any HIGH/CRITICAL.

  EC-01  CRITICAL — dominant_mental_state="suicidal" OR "suicidal" in root_causes
         → Immediate crisis referral. Do NOT delay for cause analysis.

  EC-02  HIGH — dominant_mental_state="bipolar" AND confidence > 0.60
         → Psychiatric referral before any CBT-I.
           Sleep Restriction CONTRAINDICATED (can trigger mania).

  EC-03  HIGH — dominant_mental_state="depression" AND predicted_sleep_hours > 9.0
         → Hypersomnia pattern. GP / psychiatrist referral.

  EC-04  HIGH — predicted_sleep_hours < 4.5 AND insomnia_detected=TRUE
         → PSG referral. Possible sleep apnoea.

  EC-05  HIGH — dominant_mental_state="personality disorder" AND confidence > 0.55
         → DBT / specialised psychotherapy referral.

  EC-06  MEDIUM — overall_confidence < 0.45
         → Conservative plan only. Collect more data.

  EC-07  MEDIUM — CONFLICT-4 in conflicts_detected
         → Human clinical review before recommendations.

  EC-08  MEDIUM — CONFLICT-5 detected AND both confidences > 0.65
         → Dual-diagnosis assessment.

  referral_required = TRUE  if any CRITICAL or HIGH
  referral_required = FALSE if only MEDIUM / LOW
  referral_reason   = concatenated descriptions of CRITICAL/HIGH cases

  ── FINAL REASONING REPORT SCHEMA ─────────────────────────────────────────────
  Return ONLY this JSON. No markdown. No prose. No code fences.

  {
    "user_id":              "<string>",
    "reasoning_timestamp":  "<ISO-8601>",
    "framework":            "3P Model (Spielman 1987) + DSM-5 + ICSD-3",
    "insomnia_confirmed":   <true|false>,
    "insomnia_type":        "<QUANTITATIVE|QUALITATIVE|SECONDARY|COMORBID|INCONCLUSIVE>",
    "primary_disorder":     "<string>",
    "rules_applied":        ["A1","B1","C1","D1"],
    "root_causes": [
      {
        "cause_id":          "RC-01",
        "rank":              "PRIMARY",
        "cause":             "<string>",
        "category":          "<string>",
        "3p_type":           "<string>",
        "supporting_models": ["<string>"],
        "evidence":          "<field values + rule + Neo4j graph entities>",
        "clinical_weight":   <float>,
        "modifiability":     "<HIGH|MEDIUM|LOW>",
        "rule_applied":      "<string>"
      }
    ],
    "edge_cases": [
      {
        "edge_case_id":         "EC-01",
        "pattern_detected":     "<matched values>",
        "severity":             "<CRITICAL|HIGH|MEDIUM>",
        "clinical_description": "<meaning>",
        "recommended_action":   "<action>",
        "requires_referral":    <true|false>
      }
    ],
    "reasoning_summary": "<4-5 sentences: (1) insomnia status + type,
                          (2) primary cause + evidence, (3) secondary causes,
                          (4) edge cases, (5) referral decision.>",
    "referral_required":       <true|false>,
    "referral_reason":         "<string|null>",
    "confidence_in_reasoning": <float>,
    "data_gaps":               ["<info that would improve reasoning>"]
  }
"""

REASONING_INSTRUCTIONS = "\n\n".join([
    _RULE_BASED_REASONING, _ROOT_CAUSE_RANKING, _EDGE_CASE_DETECTION
])


def build_reasoning_agent() -> Agent:
    """
    §5.3.2 — Builds the Reasoning Agent (Agent 2).

    Role in pipeline:
      Receives Unified Insomnia Profile from Correlation Agent (§5.3.1).
      Applies clinical rule sets §5.3.2.1 to identify causes.
      Ranks causes §5.3.2.2 (using Neo4j graph evidence §5.1.3.2).
      Detects edge cases §5.3.2.3.
      Passes Reasoning Report to Recommendation Agent via CrewAI (§5.4.3).
    """
    return Agent(
        role="Clinical Sleep Medicine Physician & Evidence-Based Reasoning Engine",

        goal=(
            "§5.3.2.1 Apply four rule sets (3P Model + DSM-5 + ICSD-3) to the "
            "Unified Insomnia Profile: Rule Set A confirms insomnia; Rule Sets B and C "
            "extract causes from lifestyle features and NLP/Neo4j signals; Rule Set D "
            "handles cross-signal causes. Every cause must cite its rule and field values.\n"
            "§5.3.2.2 Rank all causes using three-criterion clinical weight "
            "(convergence 0-0.50, confidence 0-0.30, modifiability 0-0.20). "
            "Enrich evidence with Neo4j graph entities (§5.1.3.2). RC-01 = PRIMARY.\n"
            "§5.3.2.3 Screen all eight edge case patterns. Set referral_required=TRUE "
            "if any CRITICAL or HIGH edge case is detected."
        ),

        backstory=(
            "You are a board-certified sleep medicine physician (AASM Fellow) and "
            "CBT-I therapist with 20 years of clinical experience in comorbid insomnia. "
            "You apply the 3P model rigorously and enrich your clinical reasoning with "
            "causal relationships from a Neo4j knowledge graph (§5.1.3.2) that links "
            "symptoms, emotions, and triggers via CAUSES / TRIGGERED_BY / ASSOCIATED_WITH "
            "edges. Every cause you identify cites the exact model fields and graph "
            "entities that support it. You never hallucinate. You never skip edge case "
            "screening. You output strictly valid JSON."
        ),

        verbose=AGENT_VERBOSE,
        allow_delegation=False,
        llm=AGENT_LLM,
    )
