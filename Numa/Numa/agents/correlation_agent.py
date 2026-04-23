"""
agents/correlation_agent.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Rapport §5.3.1  — Agent 1: Correlation Agent
         §5.3.1.1 — Model Output Aggregation
         §5.3.1.2 — Confidence Weighting
         §5.3.1.3 — Conflict Detection
         §5.3.1.4 — Unified Insomnia Profile Generation

Pipeline position : FIRST agent in CrewAI sequential pipeline.
Input  : raw outputs of §5.2 Model Layer (sleep + lifestyle + NLP)
Output : Unified Insomnia Profile JSON  →  consumed by Reasoning Agent
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

from crewai import Agent
from config import AGENT_LLM, AGENT_VERBOSE


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.1.1  MODEL OUTPUT AGGREGATION
# Extracts and normalises every relevant field from the three model outputs.
# ─────────────────────────────────────────────────────────────────────────────
_AGGREGATION = """
══ §5.3.1.1  MODEL OUTPUT AGGREGATION ══════════════════════════════════════════
You receive the real-time outputs of three ML inference modules (§5.2 Model Layer).
Extract ALL fields listed below. Record null + add to missing_signals[] if absent.

  ┌────────────────────────────────────────────────────────────────────────────┐
  │ [A] SLEEP MODEL  §5.2.1 — Binary Classifier (Insomnia: yes / no)          │
  │     Source: insomnia_combined_pipeline.ipynb + Qdrant kNN (§5.1.3.1)      │
  └────────────────────────────────────────────────────────────────────────────┘
  Extract:
    • prediction.insomnia_detected          → bool   (main insomnia label)
    • prediction.predicted_disorder         → string (disorder name)
    • prediction.confidence                 → float  (kNN vote confidence)
    • qdrant_classification.vote_counts     → dict   (label → vote count)
    • qdrant_classification.vote_confidence → float
    • best_ml_classifier.name              → string  (SVM / RF / KNN / etc.)
    • best_ml_classifier.accuracy          → float
    • best_ml_classifier.f1_score          → float
    • dataset_info.unique_disorders        → list[str]
  Derive: sleep_signal_strength = (accuracy + f1_score + confidence) / 3

  ┌────────────────────────────────────────────────────────────────────────────┐
  │ [B] LIFESTYLE MODEL  §5.2.2 — Routine Cause Classifier                    │
  │     Source: Data_Vis.ipynb  (§3.1.2 Lifestyle Dataset)                    │
  └────────────────────────────────────────────────────────────────────────────┘
  Extract:
    • prediction.predicted_sleep_hours      → float
    • prediction.sleep_quality_label        → INSUFFICIENT|BORDERLINE|ADEQUATE|EXCESSIVE
    • prediction.routine_trigger            → bool   (is a routine trigger detected?)
    • prediction.confidence                 → float  (r2_score as reliability proxy)
    • trigger_analysis.primary_cause        → string (main lifestyle cause)
    • trigger_analysis.primary_causes       → list[str]
    • trigger_analysis.secondary_causes     → list[str]
    • trigger_analysis.feature_importances  → dict   {feature: importance_float}
      Key features: WorkHours, CaffeineIntake, PhoneTime, RelaxationTime,
                    WorkoutTime, ReadingTime, Work_x_Caffeine, Screen_Time_Intensity
    • model_performance.r2_score            → float
    • model_performance.mae_hours           → float
  Derive: lifestyle_disruption = (sleep_quality_label ∈ {INSUFFICIENT, BORDERLINE})
  Derive: top_3_features = top 3 by |importance| descending

  ┌────────────────────────────────────────────────────────────────────────────┐
  │ [C] NLP MODEL  §5.2.3 — Sentiment + Cause Extraction                      │
  │     Source: nlpqdrantfinale.ipynb + neo4j_graphrag.ipynb                  │
  │     Uses: Qdrant semantic retrieval (§5.1.3.1) + Neo4j graph (§5.1.3.2)  │
  └────────────────────────────────────────────────────────────────────────────┘
  Extract:
    • prediction.dominant_mental_state      → string (depression/anxiety/stress/
                                               bipolar/suicidal/personality disorder/normal)
    • prediction.confidence                 → float  (hybrid voting confidence)
    • sentiment_analysis.primary_emotion    → string
    • sentiment_analysis.secondary_emotions → list[str]
    • root_causes_extracted                 → list[str] (from Qdrant + Neo4j triggers)
    • knowledge_graph.top_symptoms          → list[str] (from Neo4j §5.1.3.2)
    • knowledge_graph.top_emotions          → list[str]
    • knowledge_graph.top_triggers          → list[str]
    • system_evaluation.accuracy_on_test_cases → float
  Note: This model has the richest causal signal (Qdrant semantic search +
        Neo4j CAUSES / TRIGGERED_BY / ASSOCIATED_WITH graph relationships).
        Give it more weight when its confidence ≥ 0.70.
"""


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.1.2  CONFIDENCE WEIGHTING
# Dynamic weighting: penalise unreliable models, normalise, compute overall score.
# ─────────────────────────────────────────────────────────────────────────────
_WEIGHTING = """
══ §5.3.1.2  CONFIDENCE WEIGHTING ══════════════════════════════════════════════
Execute these five steps in order. Show all intermediate values in the output.

  STEP 1 — Extract raw confidence per model
    w_sleep      ← sleep_model.prediction.confidence       (kNN vote proportion)
    w_lifestyle  ← lifestyle_model.model_performance.r2_score (reliability proxy)
    w_nlp        ← nlp_model.prediction.confidence         (hybrid vote confidence)

  STEP 2 — Apply four-tier reliability penalty (independently per model)
    w < 0.40          →  w_penalised = w × 0.50   [UNRELIABLE]
    0.40 ≤ w < 0.60   →  w_penalised = w × 0.75   [UNCERTAIN]
    0.60 ≤ w < 0.75   →  w_penalised = w × 0.90   [MODERATE]
    w ≥ 0.75          →  w_penalised = w × 1.00   [HIGH SIGNAL]

  STEP 3 — If CONFLICT-3 detected (NLP normal but lifestyle disrupted):
    w_nlp_penalised = w_nlp_penalised × 0.85  (additional 15% reduction)

  STEP 4 — Normalise so weights sum to exactly 1.0
    total            = w_sleep_p + w_lifestyle_p + w_nlp_p
    w_sleep_norm     = w_sleep_p     / total
    w_lifestyle_norm = w_lifestyle_p / total
    w_nlp_norm       = w_nlp_p       / total

  STEP 5 — Compute overall_confidence and assign tier
    overall_confidence = (w_sleep_norm × w_sleep_raw)
                       + (w_lifestyle_norm × w_lifestyle_raw)
                       + (w_nlp_norm × w_nlp_raw)

    overall_confidence < 0.50  →  tier = "LOW"    (conservative plan only)
    0.50 ≤ conf < 0.70         →  tier = "MEDIUM"  (treat with caution)
    conf ≥ 0.70                →  tier = "HIGH"    (full clinical reasoning)

  Report ALL values (raw, penalised, normalised) in confidence_weighting block.
"""


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.1.3  CONFLICT DETECTION
# Five cross-model contradiction patterns — each clinically meaningful.
# ─────────────────────────────────────────────────────────────────────────────
_CONFLICTS = """
══ §5.3.1.3  CONFLICT DETECTION ════════════════════════════════════════════════
Check ALL five patterns. Document every detected conflict — never suppress one.

  CONFLICT-1  Sleep–NLP Contradiction
  ─────────────────────────────────────────────────────────────────────────────
  Trigger   : sleep_model.insomnia_detected = FALSE
              AND nlp_model.dominant_mental_state ∈ {depression, anxiety,
              stress, bipolar, suicidal}
  Meaning   : Sleep classifier sees no insomnia but NLP detects a psychiatric
              state strongly associated with sleep disruption. Insomnia is
              likely a secondary/prodromal symptom not yet captured in sleep logs.
  Resolution: nlp_confidence > sleep_confidence → flag PROBABLE insomnia
              else → flag POSSIBLE insomnia

  CONFLICT-2  Sleep–Lifestyle Contradiction  (Qualitative Insomnia)
  ─────────────────────────────────────────────────────────────────────────────
  Trigger   : sleep_model.insomnia_detected = TRUE
              AND lifestyle_model.sleep_quality_label = "ADEQUATE"
  Meaning   : Classifier detects insomnia but predicted sleep hours are adequate.
              Classic qualitative insomnia — fragmented, non-restorative sleep
              despite sufficient duration. Sleep architecture likely impaired.
  Resolution: Set insomnia_type = "QUALITATIVE"
              Flag: QUALITATIVE_INSOMNIA_SUSPECTED

  CONFLICT-3  NLP–Lifestyle Contradiction  (Behavioural Aetiology)
  ─────────────────────────────────────────────────────────────────────────────
  Trigger   : nlp_model.dominant_mental_state = "normal"
              AND lifestyle_model.sleep_quality_label ∈ {INSUFFICIENT, BORDERLINE}
  Meaning   : No psychological distress in journals but lifestyle is disrupting
              sleep. Purely behavioural aetiology (caffeine, screen time, schedule).
  Resolution: Reduce w_nlp by additional 15%. Flag: BEHAVIOURAL_AETIOLOGY_SUSPECTED

  CONFLICT-4  Global Low Confidence
  ─────────────────────────────────────────────────────────────────────────────
  Trigger   : ALL three raw confidences < 0.55
  Meaning   : Data quality insufficient across all modalities.
  Resolution: Force confidence_tier = "LOW". Flag: DATA_QUALITY_INSUFFICIENT

  CONFLICT-5  Inter-Model Label Mismatch  (Comorbidity)
  ─────────────────────────────────────────────────────────────────────────────
  Trigger   : sleep_model.predicted_disorder ≠ nlp_model.dominant_mental_state
              AND both confidences > 0.65
  Meaning   : Two high-confidence models disagree → possible comorbidity.
  Resolution: Set insomnia_type = "COMORBID". Flag: COMORBIDITY_POSSIBLE

  ── CONFLICT RECORD FORMAT (one per detected conflict):
  {
    "conflict_id":          "C-01",
    "conflict_type":        "CONFLICT-1",
    "models_involved":      ["sleep_model", "nlp_model"],
    "description":          "<specific field values that triggered it>",
    "clinical_implication": "<what it means for this user>",
    "resolution_applied":   "<adjustment made>"
  }
  If no conflicts: "conflicts_detected": []
"""


# ─────────────────────────────────────────────────────────────────────────────
# §5.3.1.4  UNIFIED INSOMNIA PROFILE — OUTPUT SCHEMA
# ─────────────────────────────────────────────────────────────────────────────
_PROFILE_SCHEMA = """
══ §5.3.1.4  UNIFIED INSOMNIA PROFILE — OUTPUT SCHEMA ══════════════════════════
Return ONLY this JSON. No markdown. No prose. No code fences.

{
  "user_id":           "<string>",
  "profile_timestamp": "<ISO-8601>",

  "insomnia_detected":  <true|false>,
  "primary_disorder":   "<string>",
  "insomnia_type":      "<QUANTITATIVE|QUALITATIVE|COMORBID|SECONDARY|UNKNOWN>",
  "overall_confidence": <float>,
  "confidence_tier":    "<LOW|MEDIUM|HIGH>",

  "confidence_weighting": {
    "sleep_model":     {"raw":<f>,"penalised":<f>,"normalised":<f>,"tier":"<string>"},
    "lifestyle_model": {"raw":<f>,"penalised":<f>,"normalised":<f>,"tier":"<string>"},
    "nlp_model":       {"raw":<f>,"penalised":<f>,"normalised":<f>,"tier":"<string>"}
  },

  "aggregated_signals": {
    "sleep_model": {
      "insomnia_detected":   <true|false|null>,
      "predicted_disorder":  "<string>",
      "confidence":          <float>,
      "classifier_accuracy": <float>,
      "f1_score":            <float>,
      "vote_counts":         {"<label>":<int>},
      "weight_applied":      <float>
    },
    "lifestyle_model": {
      "predicted_sleep_hours": <float>,
      "sleep_quality_label":   "<string>",
      "routine_trigger":       <true|false>,
      "lifestyle_disruption":  <true|false>,
      "primary_cause":         "<string>",
      "secondary_causes":      ["<string>"],
      "top_3_features":        {"<feature>":<importance>},
      "r2_score":              <float>,
      "mae_hours":             <float>,
      "weight_applied":        <float>
    },
    "nlp_model": {
      "dominant_mental_state":  "<string>",
      "primary_emotion":        "<string>",
      "secondary_emotions":     ["<string>"],
      "root_causes":            ["<string>"],
      "graph_symptoms":         ["<string>"],
      "graph_emotions":         ["<string>"],
      "graph_triggers":         ["<string>"],
      "nlp_accuracy":           <float>,
      "confidence":             <float>,
      "weight_applied":         <float>
    }
  },

  "conflicts_detected": [
    {
      "conflict_id":          "<C-01>",
      "conflict_type":        "<CONFLICT-1..5>",
      "models_involved":      ["<string>"],
      "description":          "<values that triggered>",
      "clinical_implication": "<meaning for user>",
      "resolution_applied":   "<adjustment made>"
    }
  ],

  "missing_signals": ["<dot.path.of.absent.field>"],

  "profile_summary": "<3-4 sentence clinical narrative: (1) insomnia confirmed/probable/possible
                       and type, (2) primary disorder with evidence, (3) top lifestyle triggers
                       named specifically, (4) psychological/emotional state from NLP.>",

  "flags": ["<REFERRAL_CANDIDATE|DATA_QUALITY_INSUFFICIENT|QUALITATIVE_INSOMNIA_SUSPECTED|
              BEHAVIOURAL_AETIOLOGY_SUSPECTED|COMORBIDITY_POSSIBLE|SECONDARY_INSOMNIA_SUSPECTED>"]
}
"""

# Full instructions exported to task
CORRELATION_INSTRUCTIONS = "\n\n".join([
    _AGGREGATION, _WEIGHTING, _CONFLICTS, _PROFILE_SCHEMA
])


def build_correlation_agent() -> Agent:
    """
    §5.3.1 — Builds the Correlation Agent (Agent 1).

    Role in pipeline:
      Receives outputs from §5.2 Model Layer (sleep + lifestyle + NLP).
      Applies §5.3.1.1–5.3.1.4 to produce the Unified Insomnia Profile.
      Passes result to Reasoning Agent via CrewAI context injection (§5.4.3).
    """
    return Agent(
        role="Multi-Modal Insomnia Data Correlation Specialist",

        goal=(
            "§5.3.1.1 Aggregate raw outputs of the three ML models (Sleep Binary "
            "Classifier §5.2.1, Lifestyle Routine Cause Classifier §5.2.2, NLP "
            "Mental Health Model §5.2.3) into one normalised data object. Extract "
            "every field; add absent fields to missing_signals[].\n"
            "§5.3.1.2 Apply five-step dynamic confidence weighting: extract raw "
            "confidences, apply four-tier penalties, normalise to 1.0, compute "
            "overall_confidence, assign LOW/MEDIUM/HIGH tier.\n"
            "§5.3.1.3 Check all five conflict patterns (Sleep-NLP, Sleep-Lifestyle, "
            "NLP-Lifestyle, Global Low Confidence, Label Mismatch). Document each "
            "with clinical implication and resolution.\n"
            "§5.3.1.4 Produce a single Unified Insomnia Profile JSON that is the "
            "sole input to Agent 2 (Reasoning Agent)."
        ),

        backstory=(
            "You are a senior clinical data scientist specialising in multi-modal "
            "signal fusion for digital sleep medicine. You combine outputs from a "
            "Qdrant-backed sleep classifier (§5.1.3.1), a lifestyle regression model, "
            "and an NLP/GraphRAG psychiatric classifier that leverages both Qdrant "
            "semantic search and a Neo4j causal knowledge graph (§5.1.3.2).\n\n"
            "Your discipline: aggregate ALL fields before interpreting any, apply "
            "confidence penalties mathematically, detect ALL five conflict types, "
            "and synthesise everything into a 3-4 sentence clinical narrative. "
            "You output ONLY valid JSON — no prose, no markdown, no code fences."
        ),

        verbose=AGENT_VERBOSE,
        allow_delegation=False,
        llm=AGENT_LLM,
    )
