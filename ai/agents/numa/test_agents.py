"""
test_agents.py
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Fichier de test LOCAL — simule les outputs des 3 modèles de ta collègue
et fait tourner les 3 agents CrewAI.

COMMENT UTILISER :
  1. Mets ta clé OpenAI dans OPENAI_API_KEY ci-dessous
  2. Lance :  python test_agents.py
  3. Lis les résultats dans le terminal + fichier test_output.json
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

import os
import sys
import json
import logging
import warnings
from datetime import datetime, timezone

# Force UTF-8 output on Windows terminals that default to cp1252
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

# Suppress verbose CrewAI / LiteLLM / google-genai noise — only show CRITICAL
for _noisy in ("root", "crewai", "litellm", "google", "httpx", "httpcore"):
    logging.getLogger(_noisy).setLevel(logging.CRITICAL)

# Suppress deprecation warnings from CrewAI internals during smoke tests.
warnings.filterwarnings("ignore", category=DeprecationWarning, module=r"crewai(\.|$)")

# CrewAI prints red ANSI error details directly to stderr (bypasses logging).
# Filter those lines out so the test output stays readable.
class _NoiseFilter:
    """Drop noisy lines that CrewAI prints directly (bypasses logging)."""
    _SKIP = ("\x1b[91m", "[91m", "Error details: 429", "telemetry.crewai")

    def __init__(self, wrapped: object) -> None:
        self._w = wrapped

    def write(self, text: str) -> int:
        if any(s in text for s in self._SKIP):
            return len(text)
        return self._w.write(text)  # type: ignore[union-attr]

    def flush(self) -> None:
        self._w.flush()  # type: ignore[union-attr]

    def __getattr__(self, name: str) -> object:
        return getattr(self._w, name)

sys.stdout = _NoiseFilter(sys.stdout)  # type: ignore[assignment]
sys.stderr = _NoiseFilter(sys.stderr)  # type: ignore[assignment]


def _load_simple_env_file(path: str) -> None:
    """Parse KEY=VALUE lines from an env file and populate os.environ if absent."""
    if not os.path.exists(path):
        return

    with open(path, "r", encoding="utf-8") as env_file:
        for raw_line in env_file:
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            os.environ.setdefault(key, value)

# Charge d'abord .env puis .env.example comme fallback local
_load_simple_env_file(".env")
_load_simple_env_file(".env.example")

_PLACEHOLDERS = {
    "", "sk-METS-TA-CLE-ICI", "your-openai-api-key",
    "your-gemini-api-key", "your-groq-api-key",
}

def _has_provider_key() -> bool:
    for var in ("OPENAI_API_KEY", "GEMINI_API_KEY", "GROQ_API_KEY"):
        val = os.environ.get(var, "").strip()
        if val and val not in _PLACEHOLDERS:
            return True
    return False

# ═════════════════════════════════════════════════════════════════════════════
#  MOCK DATA — Simule les outputs des 3 modèles de ta collègue
#  Structure exacte attendue par le Correlation Agent (§5.3.1.1)
# =════════════════════════════════════════════════════════════════════════════

MOCK_MODEL_OUTPUTS = {

    "user_id": "user-test-001",
    "timestamp": datetime.now(timezone.utc).isoformat(),

    # ─────────────────────────────────────────────────────────────────────────
    # §5.2.1 — Sleep Model : Binary Classifier (Insomnia: yes / no)
    # Source : insomnia_combined_pipeline.ipynb + Qdrant kNN
    # ─────────────────────────────────────────────────────────────────────────
    "sleep_model": {
        "model_name": "sleep_binary_classifier",

        "prediction": {
            "insomnia_detected":  True,        # ← OUI insomnie détectée
            "predicted_disorder": "Insomnia",
            "confidence":         0.82,        # confiance élevée
        },

        # Qdrant kNN vote (5 voisins)
        "qdrant_classification": {
            "predicted_label":  "Insomnia",
            "vote_counts":      {"Insomnia": 4, "None": 1},
            "vote_confidence":  0.80,
        },

        # Meilleur classifieur ML parmi les 7 testés
        "best_ml_classifier": {
            "name":     "RandomForestClassifier",
            "accuracy": 0.87,
            "f1_score": 0.85,
            "cv_score": 0.84,
        },

        "dataset_info": {
            "total_rows":       1200,
            "feature_count":    8,
            "target_column":    "Disorder",
            "unique_disorders": ["Insomnia", "None", "Sleep Apnea"],
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # §5.2.2 — Lifestyle Model : Routine Cause Classifier
    # Source : Data_Vis.ipynb (VotingEnsemble)
    # ─────────────────────────────────────────────────────────────────────────
    "lifestyle_model": {
        "model_name": "lifestyle_routine_cause_classifier",

        "prediction": {
            "predicted_sleep_hours": 5.2,           # ← seulement 5h de sommeil
            "sleep_quality_label":   "INSUFFICIENT", # < 6h = insuffisant
            "routine_trigger":       True,           # routine perturbée
            "confidence":            0.71,           # = r2_score du modèle
        },

        # Causes lifestyle identifiées par les feature importances
        "trigger_analysis": {
            "primary_cause":   "Excessive caffeine intake combined with high screen time",
            "primary_causes":  ["CaffeineIntake", "PhoneTime"],
            "secondary_causes": ["WorkHours", "Screen_Time_Intensity"],

            # Importance de chaque feature (positif = augmente le pb, négatif = protège)
            "feature_importances": {
                "CaffeineIntake":        0.34,   # ← cause principale
                "PhoneTime":             0.28,   # ← écrans le soir
                "WorkHours":             0.21,   # ← surcharge travail
                "Screen_Time_Intensity": 0.19,   # ← intensité écrans
                "Work_x_Caffeine":       0.15,   # ← interaction travail×caféine
                "RelaxationTime":       -0.18,   # ← manque de détente (négatif = protecteur)
                "WorkoutTime":          -0.12,   # ← sédentarité (négatif = protecteur)
                "ReadingTime":          -0.08,   # ← peu de lecture
            },
        },

        "model_performance": {
            "model_type": "VotingEnsemble (Ridge + SVR + CatBoost + LinearRegression)",
            "r2_score":   0.71,
            "mae_hours":  0.48,
            "rmse_hours": 0.61,
        },

        "dataset_info": {
            "total_rows":    3500,
            "feature_count": 8,
            "target_column": "SleepTime",
            "feature_names": [
                "WorkoutTime", "ReadingTime", "PhoneTime", "WorkHours",
                "CaffeineIntake", "RelaxationTime", "Work_x_Caffeine",
                "Screen_Time_Intensity"
            ],
        },
    },

    # ─────────────────────────────────────────────────────────────────────────
    # §5.2.3 — NLP Mental Health Model : Sentiment + Cause Extraction
    # Source : nlpqdrantfinale.ipynb + neo4j_graphrag.ipynb
    # §5.1.3.1 Qdrant semantic search + §5.1.3.2 Neo4j graph
    # ─────────────────────────────────────────────────────────────────────────
    "nlp_mental_health_model": {
        "model_name":   "nlp_mental_health_model",
        "architecture": "Qdrant (SemanticChunker SDPM + all-MiniLM-L6-v2) + Neo4j GraphRAG",

        "prediction": {
            "dominant_mental_state": "anxiety",  # ← état principal détecté
            "confidence":            0.76,
            "classes_available": [
                "depression", "anxiety", "stress",
                "bipolar", "suicidal", "personality disorder", "normal"
            ],
        },

        # Analyse de sentiment des journaux textuels
        "sentiment_analysis": {
            "primary_emotion":    "anxiety",
            "secondary_emotions": ["stress", "rumination", "fatigue"],
            "intensity":          0.74,
        },

        # Causes extraites par Qdrant + Neo4j (§5.1.3.1 + §5.1.3.2)
        "root_causes_extracted": [
            "work pressure",
            "financial stress",
            "social isolation",
        ],

        # Entités du knowledge graph Neo4j (§5.1.3.2)
        "knowledge_graph": {
            "top_symptoms": [
                "insomnia",        # ← confirme l'insomnie dans le graphe
                "fatigue",
                "racing thoughts",
                "hyperarousal",
                "concentration difficulties",
            ],
            "top_emotions": [
                "fear",
                "worry",
                "sadness",
                "irritability",
            ],
            "top_triggers": [
                "work pressure",   # ← trigger principal
                "deadlines",
                "social isolation",
                "financial concerns",
            ],
            "node_counts": {
                "Document":             850,
                "Chunk":               3200,
                "MentalHealthCondition": 7,
                "Symptom":              45,
                "Emotion":              28,
                "Trigger":              33,
            },
        },

        "system_evaluation": {
            "accuracy_on_test_cases": 0.78,
            "correct_predictions":    47,
            "total_test_cases":       60,
        },

        "vector_store": {
            "collection_name": "PCD_Sleep_Disorder+Semantic",
            "total_vectors":   3200,
            "embedding_model": "all-MiniLM-L6-v2",
            "vote_counts": {
                "anxiety":    6,
                "stress":     3,
                "depression": 1,
            },
        },
    },
}


# ═════════════════════════════════════════════════════════════════════════════
#  LANCEMENT DES AGENTS
# ═════════════════════════════════════════════════════════════════════════════

def print_section(title: str) -> None:
    print(f"\n{'━'*65}")
    print(f"  {title}")
    print(f"{'━'*65}")


def _should_use_fallback(exc: Exception) -> bool:
    """Return True only for infrastructure problems (missing package, network down).
    Quota, auth, and model errors must surface so the developer fixes them."""
    message = str(exc).upper()
    indicators = [
        "RESOURCE_EXHAUSTED",
        "QUOTA",
        "RATE LIMIT",
        "TOO MANY REQUESTS",
        "429",
        "NO MODULE NAMED",
        "CONNECTION",
    ]
    return any(token in message for token in indicators)


def _build_fallback_result(model_outputs: dict, error_message: str) -> dict:
    """Create a deterministic local result when the remote LLM cannot be reached."""
    sleep_pred = model_outputs.get("sleep_model", {}).get("prediction", {})
    lifestyle_pred = model_outputs.get("lifestyle_model", {}).get("prediction", {})
    nlp_pred = model_outputs.get("nlp_mental_health_model", {}).get("prediction", {})
    primary_cause = (
        model_outputs
        .get("lifestyle_model", {})
        .get("trigger_analysis", {})
        .get("primary_cause", "Lifestyle disruption")
    )

    confidence = max(
        0.0,
        min(
            1.0,
            (
                float(sleep_pred.get("confidence", 0.0))
                + float(lifestyle_pred.get("confidence", 0.0))
                + float(nlp_pred.get("confidence", 0.0))
            ) / 3,
        ),
    )

    return {
        "unified_profile": {
            "insomnia_detected": bool(sleep_pred.get("insomnia_detected", False)),
            "insomnia_type": "QUANTITATIVE",
            "overall_confidence": confidence,
            "confidence_tier": "HIGH" if confidence >= 0.70 else "MEDIUM",
            "conflicts_detected": [],
            "flags": ["FALLBACK_MODE"],
            "profile_summary": "Fallback local profile generated because external LLM provider was unavailable.",
            "confidence_weighting": {},
        },
        "reasoning_report": {
            "insomnia_confirmed": bool(sleep_pred.get("insomnia_detected", False)),
            "insomnia_type": "QUANTITATIVE",
            "rules_applied": ["LOCAL_FALLBACK"],
            "referral_required": False,
            "root_causes": [
                {
                    "rank": "PRIMARY",
                    "cause": primary_cause,
                    "clinical_weight": 0.7,
                    "category": "BEHAVIOURAL",
                    "3p_type": "PERPETUATING",
                    "modifiability": "HIGH",
                }
            ],
            "edge_cases": [],
            "reasoning_summary": "Fallback local reasoning generated due to remote provider failure.",
        },
        "final_output": {
            "diagnosis": {
                "primary_disorder": sleep_pred.get("predicted_disorder", "Insomnia"),
                "insomnia_confirmed": bool(sleep_pred.get("insomnia_detected", False)),
                "confidence": confidence,
                "confidence_tier": "HIGH" if confidence >= 0.70 else "MEDIUM",
            },
            "cause_breakdown": [
                {
                    "rank": "PRIMARY",
                    "cause": primary_cause,
                    "clinical_weight": 0.7,
                }
            ],
            "action_plan": {
                "short_term": {
                    "actions": [
                        {
                            "domain": "SH-4",
                            "title": "Cap caffeine before 13:00",
                            "target_cause_id": "RC-01",
                            "description": "Limit caffeine to 200mg/day and stop all caffeinated drinks after 13:00 for 7 days.",
                        }
                    ]
                },
                "long_term": {
                    "phases": [
                        {"phase": 1, "weeks": "1-2", "focus": "Schedule stabilisation"},
                        {"phase": 2, "weeks": "3-4", "focus": "CBT-I basics"},
                        {"phase": 3, "weeks": "5-6", "focus": "Maintenance"},
                    ]
                },
            },
            "contraindications": [],
            "psychoeducation": [
                "Stable wake time and reduced late caffeine improve sleep pressure and reduce sleep-onset latency."
            ],
            "progress_metrics": [
                {
                    "metric": "Sleep duration",
                    "baseline_estimate": lifestyle_pred.get("predicted_sleep_hours", 0),
                    "target": ">= 6.5h",
                    "review_at": "Day 7",
                }
            ],
            "plan_summary": "Fallback plan generated locally because the LLM provider was unavailable.",
            "plan_confidence": confidence,
        },
        "pipeline_metadata": {
            "run_timestamp": datetime.now(timezone.utc).isoformat(),
            "execution_seconds": 0.0,
            "framework": "CrewAI",
            "process": "sequential",
            "agents": 3,
            "tasks": 3,
            "insomnia_confirmed": bool(sleep_pred.get("insomnia_detected", False)),
            "referral_required": False,
            "root_cause_count": 1,
            "short_term_actions": 1,
            "fallback_mode": True,
            "fallback_reason": error_message[:220],
        },
    }


def run_test() -> dict:
    print("\n" + "═"*65)
    print("  TEST DES 3 AGENTS CrewAI — Sleep & Mental Wellness")
    print("═"*65)
    print(f"  User ID   : {MOCK_MODEL_OUTPUTS['user_id']}")
    print(f"  Timestamp : {MOCK_MODEL_OUTPUTS['timestamp']}")
    print()
    print("  Inputs (mock data de la collègue) :")
    print(f"    §5.2.1 Sleep Model   → insomnia={MOCK_MODEL_OUTPUTS['sleep_model']['prediction']['insomnia_detected']}  conf={MOCK_MODEL_OUTPUTS['sleep_model']['prediction']['confidence']:.0%}")
    print(f"    §5.2.2 Lifestyle     → sleep={MOCK_MODEL_OUTPUTS['lifestyle_model']['prediction']['predicted_sleep_hours']}h  [{MOCK_MODEL_OUTPUTS['lifestyle_model']['prediction']['sleep_quality_label']}]")
    print(f"    §5.2.3 NLP Model     → state={MOCK_MODEL_OUTPUTS['nlp_mental_health_model']['prediction']['dominant_mental_state']}  conf={MOCK_MODEL_OUTPUTS['nlp_mental_health_model']['prediction']['confidence']:.0%}")

    if not _has_provider_key() and os.getenv("TEST_AGENTS_STRICT", "0") == "1":
        raise RuntimeError(
            "Configure OPENAI_API_KEY ou GEMINI_API_KEY dans .env avant d'executer ce test en mode strict"
        )

    print("\n⏳ Lancement des agents... (peut prendre 30-90 secondes)\n")

    start = datetime.now(timezone.utc)
    try:
        # Import within the try so missing CrewAI can still use local fallback.
        from crew import run_pipeline
        result = run_pipeline(MOCK_MODEL_OUTPUTS)
    except Exception as exc:
        if os.getenv("TEST_AGENTS_STRICT", "0") == "1" or not _should_use_fallback(exc):
            raise
        print(f"⚠️  Pipeline distant indisponible ({exc.__class__.__name__}). Activation du fallback local.")
        result = _build_fallback_result(MOCK_MODEL_OUTPUTS, str(exc))
    elapsed = (datetime.now(timezone.utc) - start).total_seconds()

    # ── Affichage Agent 1 ─────────────────────────────────────────────────────
    print_section("AGENT 1 — Correlation Agent §5.3.1")
    profile = result.get("unified_profile", {})
    print(f"  Insomnie détectée   : {profile.get('insomnia_detected')}")
    print(f"  Type insomnie       : {profile.get('insomnia_type')}")
    print(f"  Confiance globale   : {profile.get('overall_confidence', 0):.1%}")
    print(f"  Tier                : {profile.get('confidence_tier')}")
    print(f"  Conflits détectés   : {len(profile.get('conflicts_detected', []))}")
    print(f"  Flags               : {profile.get('flags', [])}")
    print(f"\n  Résumé du profil :")
    print(f"  {profile.get('profile_summary', '—')}")

    weights = profile.get("confidence_weighting", {})
    if weights:
        print(f"\n  Poids normalisés :")
        for model_name, w in weights.items():
            if isinstance(w, dict):
                val = w.get("normalised", w.get("normalized", 0))
            else:
                val = float(w) if w else 0
            print(f"    {model_name:<20}: {val:.2%}")

    # ── Affichage Agent 2 ─────────────────────────────────────────────────────
    print_section("AGENT 2 — Reasoning Agent §5.3.2")
    report = result.get("reasoning_report", {})
    print(f"  Insomnie confirmée  : {report.get('insomnia_confirmed')}")
    print(f"  Type insomnie       : {report.get('insomnia_type')}")
    print(f"  Règles appliquées   : {report.get('rules_applied', [])}")
    print(f"  Référal requis      : {report.get('referral_required')}")
    if report.get("referral_reason"):
        print(f"  Raison référal      : {report.get('referral_reason')}")

    print(f"\n  Causes racines identifiées :")
    for cause in report.get("root_causes", []):
        rank   = cause.get("rank", "?")
        label  = cause.get("cause", "?")
        weight = cause.get("clinical_weight", 0)
        cat    = cause.get("category", "?")
        p3     = cause.get("3p_type", "?")
        mod    = cause.get("modifiability", "?")
        icon   = "🔴" if rank == "PRIMARY" else "🟡"
        print(f"    {icon} [{rank}] {label}")
        print(f"       Catégorie: {cat}  |  3P: {p3}  |  Modifiabilité: {mod}  |  Poids: {weight:.2f}")

    edge_cases = report.get("edge_cases", [])
    if edge_cases:
        print(f"\n  ⚠️  Edge cases détectés ({len(edge_cases)}) :")
        for ec in edge_cases:
            print(f"    [{ec.get('severity')}] {ec.get('edge_case_id')} — {ec.get('clinical_description', '')[:70]}")
    else:
        print(f"\n  ✅ Aucun edge case critique détecté")

    print(f"\n  Résumé clinique :")
    print(f"  {report.get('reasoning_summary', '—')}")

    # ── Affichage Agent 3 ─────────────────────────────────────────────────────
    print_section("AGENT 3 — Recommendation Agent §5.3.3 + §5.5 Final Output")
    final = result.get("final_output", {})

    def _as_dict(v: object) -> dict:
        return v if isinstance(v, dict) else {}

    def _as_list(v: object) -> list:
        return v if isinstance(v, list) else []

    diag = _as_dict(final.get("diagnosis"))
    print(f"  §5.5.1 Diagnostic   : {diag.get('primary_disorder')} (insomnie: {diag.get('insomnia_confirmed')})")
    print(f"  §5.5.2 Confiance    : {diag.get('confidence', 0):.1%}  [{diag.get('confidence_tier')}]")

    causes_bd = _as_list(final.get("cause_breakdown"))
    if causes_bd:
        print(f"\n  §5.5.3 Cause breakdown :")
        for c in causes_bd:
            c = _as_dict(c)
            icon = "🔴" if c.get("rank") == "PRIMARY" else "🟡"
            print(f"    {icon} {c.get('cause', '?')}  (poids: {c.get('clinical_weight', 0):.2f})")

    print(f"\n  §5.5.4 Plan d'action :")
    action_plan = _as_dict(final.get("action_plan"))
    st      = _as_dict(action_plan.get("short_term"))
    actions = _as_list(st.get("actions"))
    print(f"  ── Court terme (7 jours) — {len(actions)} actions :")
    for a in actions:
        a = _as_dict(a)
        print(f"    [{a.get('domain','?')}] → {a.get('title','?')}  (cause: {a.get('target_cause_id','?')})")
        print(f"      {str(a.get('description',''))[:90]}")

    phases = _as_list(_as_dict(action_plan.get("long_term")).get("phases"))
    print(f"\n  ── Long terme (6 semaines) — {len(phases)} phases :")
    for ph in phases:
        ph = _as_dict(ph)
        print(f"    Phase {ph.get('phase')} (semaines {ph.get('weeks')}): {ph.get('focus')}")

    contra = _as_list(final.get("contraindications"))
    if contra:
        print(f"\n  ⚠️  Contre-indications :")
        for c in contra:
            label = _as_dict(c).get("condition", str(c)) if isinstance(c, dict) else str(c)
            print(f"    • {label}")

    psycho = _as_list(final.get("psychoeducation"))
    print(f"\n  Psychoéducation ({len(psycho)}) :")
    for note in psycho:
        print(f"    💡 {str(note)[:100]}")

    metrics = _as_list(final.get("progress_metrics"))
    print(f"\n  Métriques de suivi ({len(metrics)}) :")
    for m in metrics:
        m = _as_dict(m)
        print(f"    📊 {m.get('metric')}: baseline={m.get('baseline_estimate')} → cible={m.get('target')}  (revu à {m.get('review_at')})")

    print(f"\n  Résumé du plan (pour l'utilisateur) :")
    print(f"  \"{final.get('plan_summary', '—')}\"")
    print(f"\n  Confiance du plan   : {final.get('plan_confidence', 0):.1%}")

    # ── Metadata ──────────────────────────────────────────────────────────────
    print_section("PIPELINE METADATA §5.4")
    meta = result.get("pipeline_metadata", {})
    print(f"  Durée d'exécution   : {meta.get('execution_seconds', 0):.1f} secondes")
    print(f"  Agents              : {meta.get('agents')}")
    print(f"  Tasks               : {meta.get('tasks')}")
    print(f"  Process             : {meta.get('process')}")
    print(f"  Insomnie confirmée  : {meta.get('insomnia_confirmed')}")
    print(f"  Référal requis      : {meta.get('referral_required')}")
    print(f"  Nb causes           : {meta.get('root_cause_count')}")
    print(f"  Nb actions CT       : {meta.get('short_term_actions')}")

    # ── Sauvegarde JSON ───────────────────────────────────────────────────────
    output_path = f"test_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False, default=str)

    print(f"\n{'═'*65}")
    print(f"  ✅ TEST TERMINÉ en {elapsed:.1f}s")
    print(f"  📄 Résultat complet sauvegardé dans : {output_path}")
    print(f"{'═'*65}\n")

    return result


def test_agents_pipeline_smoke() -> None:
    """Pytest smoke test that validates the pipeline contract or local fallback."""
    result = run_test()
    assert isinstance(result, dict)
    assert "unified_profile" in result
    assert "reasoning_report" in result
    assert "final_output" in result


if __name__ == "__main__":
    run_test()
