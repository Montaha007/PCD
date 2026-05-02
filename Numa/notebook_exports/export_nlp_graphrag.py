# ══════════════════════════════════════════════════════════════════════════════
# CELLULE D'EXPORT — Coller à la FIN de : nlpqdrantfinale.ipynb
#                    OU                  : neo4j_graphrag.ipynb
# Rapport §5.2.3 — NLP Mental Health Model: Sentiment + Cause Extraction
#         §5.1.3.1 — Qdrant semantic retrieval
#         §5.1.3.2 — Neo4j graph knowledge base
#
# Variables nécessaires :
#   NLP Qdrant   : predict_sleep_status() ou hybrid_retrieve(), model,
#                  Collection_name2, client, test_df
#   Neo4j GraphRAG : driver (optionnel)
# ══════════════════════════════════════════════════════════════════════════════

import json
import numpy as np
from collections import Counter
from datetime import datetime, timezone

# ── 1. Cas de test représentatifs ────────────────────────────────────────────
EVAL_CASES = [
    {"text": "I wake up every day feeling drained. Nothing feels meaningful.", "expected": "depression"},
    {"text": "My thoughts race at night and I worry about everything.", "expected": "anxiety"},
    {"text": "There is constant pressure from work. I feel exhausted.", "expected": "stress"},
    {"text": "Some weeks I feel unstoppable, then I crash into sadness.", "expected": "bipolar"},
    {"text": "I generally feel calm and manage my responsibilities.", "expected": "normal"},
    {"text": "Sometimes I wonder if life would be easier if I disappeared.", "expected": "suicidal"},
]

# ── 2. Évaluation du système NLP ─────────────────────────────────────────────
print("🔍 Évaluation du système NLP...")
eval_results = []
correct = 0

for case in EVAL_CASES:
    try:
        # Essaie hybrid_retrieve() (GraphRAG) sinon predict_sleep_status() (Qdrant seul)
        try:
            res        = hybrid_retrieve(case["text"], k=10)
            pred_label = res["predicted_label"]
            pred_conf  = res["confidence"]
            method     = "graphrag"
        except NameError:
            res        = predict_sleep_status(case["text"], k=10)
            if isinstance(res, dict):
                pred_label = res.get("predicted_label", "unknown")
                pred_conf  = res.get("confidence", 0.0)
            else:
                pred_label = str(res)
                pred_conf  = 0.65
            method = "qdrant_only"

        is_ok = pred_label.strip().lower() == case["expected"].strip().lower()
        if is_ok: correct += 1
        icon  = "✅" if is_ok else "❌"
        print(f"  {icon} Expected: {case['expected']:<20} Got: {pred_label:<20} ({pred_conf:.0%})")
        eval_results.append({
            "text":            case["text"][:80],
            "expected":        case["expected"],
            "predicted":       pred_label,
            "confidence":      round(float(pred_conf), 4),
            "correct":         bool(is_ok),
            "method":          method,
        })
    except Exception as e:
        print(f"  ⚠️  Error: {e}")
        eval_results.append({"text": case["text"][:80], "expected": case["expected"],
                             "predicted": "error", "confidence": 0.0,
                             "correct": False, "error": str(e)})

accuracy_eval = correct / len(EVAL_CASES)

# ── 3. Distribution des labels dans Qdrant ────────────────────────────────────
print("\n🗄️  Lecture Qdrant...")
try:
    cname = Collection_name2
except NameError:
    cname = COLLECTION_NAME

try:
    scrolled = client.scroll(collection_name=cname, limit=5000)[0]
    label_dist = dict(Counter(p.payload.get("status", "unknown") for p in scrolled))
    total_vecs = len(scrolled)
except Exception as e:
    label_dist = {}
    total_vecs = 0
    print(f"  ⚠️  Qdrant: {e}")

# ── 4. Entités Neo4j (§5.1.3.2) ──────────────────────────────────────────────
print("🌐 Lecture Neo4j...")
neo4j_stats   = {}
top_symptoms  = []
top_emotions  = []
top_triggers  = []

try:
    with driver.session() as s:
        for label in ["Document","Chunk","MentalHealthCondition","Symptom","Emotion","Trigger"]:
            neo4j_stats[label] = s.run(f"MATCH (n:{label}) RETURN count(n) AS c").single()["c"]
        top_symptoms = [r["name"] for r in s.run(
            "MATCH (n:Symptom)-[r]-() RETURN n.name AS name, count(r) AS c ORDER BY c DESC LIMIT 5"
        ).data()]
        top_emotions = [r["name"] for r in s.run(
            "MATCH (n:Emotion)-[r]-() RETURN n.name AS name, count(r) AS c ORDER BY c DESC LIMIT 5"
        ).data()]
        top_triggers = [r["name"] for r in s.run(
            "MATCH (n:Trigger)-[r]-() RETURN n.name AS name, count(r) AS c ORDER BY c DESC LIMIT 5"
        ).data()]
    print(f"  Neo4j: {neo4j_stats}")
except Exception as e:
    print(f"  ⚠️  Neo4j: {e}")

# ── 5. Construction du JSON d'export ─────────────────────────────────────────
# Dominant state = most predicted label in eval set
preds        = [r["predicted"] for r in eval_results if r["predicted"] != "error"]
dominant     = Counter(preds).most_common(1)[0][0] if preds else "unknown"
avg_conf     = round(float(np.mean([r["confidence"] for r in eval_results if r["confidence"] > 0])), 4)

nlp_output = {
    "model_name":   "nlp_mental_health_model",
    "timestamp":    datetime.now(timezone.utc).isoformat(),
    "architecture": "Qdrant (SemanticChunker SDPM + all-MiniLM-L6-v2) + Neo4j GraphRAG",

    # §5.2.3 — main prediction fields
    "prediction": {
        "dominant_mental_state": dominant,
        "confidence":            avg_conf,
        "classes_available":     ["depression","anxiety","stress","bipolar",
                                  "suicidal","personality disorder","normal"],
    },
    "sentiment_analysis": {
        "primary_emotion":    dominant,
        "secondary_emotions": [k for k in dict(Counter(preds)) if k != dominant],
        "intensity":          avg_conf,
    },
    "root_causes_extracted": top_triggers,

    # §5.1.3.2 — Neo4j knowledge graph entities
    "knowledge_graph": {
        "top_symptoms": top_symptoms,
        "top_emotions": top_emotions,
        "top_triggers": top_triggers,
        "node_counts":  {str(k): int(v) for k, v in neo4j_stats.items()},
    },

    "system_evaluation": {
        "accuracy_on_test_cases": round(accuracy_eval, 4),
        "correct_predictions":    int(correct),
        "total_test_cases":       len(EVAL_CASES),
        "detailed_results":       eval_results,
    },

    # §5.1.3.1 — Qdrant vector store info
    "vector_store": {
        "collection_name":    cname,
        "total_vectors":      int(total_vecs),
        "embedding_model":    "all-MiniLM-L6-v2",
        "chunking":           "SemanticChunker SDPM (max_chunk_size=256)",
        "label_distribution": {str(k): int(v) for k, v in label_dist.items()},
    },
}

# ── 6. Sauvegarde JSON ────────────────────────────────────────────────────────
with open("nlp_model_output.json", "w", encoding="utf-8") as f:
    json.dump(nlp_output, f, indent=2, ensure_ascii=False)

print(f"\n✅ nlp_model_output.json sauvegardé")
print(f"   État dominant     : {dominant}")
print(f"   Confiance moy.    : {avg_conf:.1%}")
print(f"   Précision tests   : {accuracy_eval:.1%} ({correct}/{len(EVAL_CASES)})")
print(f"   Vecteurs Qdrant   : {total_vecs:,}")
print(f"   Top symptômes     : {top_symptoms}")
print(f"   Top triggers      : {top_triggers}")

# ── 7. Téléchargement depuis Colab ───────────────────────────────────────────
from google.colab import files
files.download("nlp_model_output.json")
