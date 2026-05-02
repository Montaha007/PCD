# ══════════════════════════════════════════════════════════════════════════════
# CELLULE D'EXPORT — Coller à la FIN de : insomnia_combined_pipeline.ipynb
# Rapport §5.2.1 — Sleep Model: Binary Classifier (Insomnia: Yes / No)
#
# Variables nécessaires (déjà définies dans ton notebook) :
#   best_model_name, comparison_df, models, y_test, X_test_scaled,
#   scaler, X, target_col, df, QUERY_IDX, predicted_label, true_label, vote_counts
# ══════════════════════════════════════════════════════════════════════════════

import json
import joblib
import numpy as np
from datetime import datetime, timezone
from sklearn.metrics import precision_score, recall_score, f1_score

# ── 1. Sauvegarde des modèles (.pkl) ──────────────────────────────────────────
best_ml_model = models[best_model_name]
joblib.dump(best_ml_model, "sleep_classifier.pkl")
joblib.dump(scaler,        "sleep_scaler.pkl")
print("✅ sleep_classifier.pkl sauvegardé")
print("✅ sleep_scaler.pkl sauvegardé")

# ── 2. Calcul des métriques ───────────────────────────────────────────────────
y_pred_best  = best_ml_model.predict(X_test_scaled)
accuracy_val = float(comparison_df.iloc[0]["Accuracy"])
precision_val= float(precision_score(y_test, y_pred_best, average="weighted", zero_division=0))
recall_val   = float(recall_score(y_test, y_pred_best, average="weighted", zero_division=0))
f1_val       = float(f1_score(y_test, y_pred_best, average="weighted", zero_division=0))
cv_score_val = float(comparison_df.iloc[0]["Mean CV Score"])

# ── 3. Résultats Qdrant kNN ───────────────────────────────────────────────────
qdrant_votes  = dict(vote_counts)
knn_correct   = (str(predicted_label).strip().lower() == str(true_label).strip().lower())
knn_conf      = float(max(qdrant_votes.values()) / sum(qdrant_votes.values())) if qdrant_votes else 0.0

# ── 4. Construction du JSON d'export ─────────────────────────────────────────
sleep_output = {
    "model_name": "sleep_binary_classifier",
    "timestamp":  datetime.now(timezone.utc).isoformat(),
    "prediction": {
        "insomnia_detected":  knn_correct,
        "predicted_disorder": str(predicted_label),
        "confidence":         round((accuracy_val + knn_conf) / 2, 4),
    },
    "qdrant_classification": {
        "true_label":        str(true_label),
        "predicted_label":   str(predicted_label),
        "vote_counts":       {str(k): int(v) for k, v in qdrant_votes.items()},
        "vote_confidence":   round(knn_conf, 4),
        "correct_prediction": knn_correct,
    },
    "best_ml_classifier": {
        "name":      str(best_model_name),
        "accuracy":  round(accuracy_val,  4),
        "precision": round(precision_val, 4),
        "recall":    round(recall_val,    4),
        "f1_score":  round(f1_val,        4),
        "cv_score":  round(cv_score_val,  4),
    },
    "all_models_comparison": [
        {
            "model":    row["Model"],
            "accuracy": round(float(row["Accuracy"]), 4),
            "f1_score": round(float(row["F1-Score"]),  4),
            "cv_score": round(float(row["Mean CV Score"]), 4),
        }
        for _, row in comparison_df.iterrows()
    ],
    "dataset_info": {
        "total_rows":       int(len(df)),
        "feature_count":    int(X.shape[1]),
        "target_column":    str(target_col),
        "unique_disorders": [str(c) for c in df[target_col].unique().tolist()],
    },
}

# ── 5. Sauvegarde JSON ────────────────────────────────────────────────────────
with open("sleep_model_output.json", "w", encoding="utf-8") as f:
    json.dump(sleep_output, f, indent=2, ensure_ascii=False)

print("\n✅ sleep_model_output.json sauvegardé")
print(f"   Insomnie détectée : {sleep_output['prediction']['insomnia_detected']}")
print(f"   Disorder prédit   : {sleep_output['prediction']['predicted_disorder']}")
print(f"   Confiance         : {sleep_output['prediction']['confidence']:.1%}")
print(f"   Meilleur modèle   : {best_model_name}  acc={accuracy_val:.2%}")

# ── 6. Téléchargement depuis Colab ───────────────────────────────────────────
from google.colab import files
files.download("sleep_classifier.pkl")
files.download("sleep_scaler.pkl")
files.download("sleep_model_output.json")
