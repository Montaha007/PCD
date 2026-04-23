# ══════════════════════════════════════════════════════════════════════════════
# CELLULE D'EXPORT — Coller à la FIN de : Data_Vis.ipynb
# Rapport §5.2.2 — Lifestyle Model: Routine Cause Classifier
#
# Variables nécessaires (déjà définies dans ton notebook) :
#   voting_ensemble, ensemble, best_model, scaler, X, X_train, X_test,
#   y_train, y_test, results_df, df
# ══════════════════════════════════════════════════════════════════════════════

import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.inspection import permutation_importance

# ── 1. Sauvegarde des modèles (.pkl) ──────────────────────────────────────────
joblib.dump(voting_ensemble, "lifestyle_model.pkl")
joblib.dump(scaler,          "lifestyle_scaler.pkl")
print("✅ lifestyle_model.pkl sauvegardé")
print("✅ lifestyle_scaler.pkl sauvegardé")

# ── 2. Métriques sur le test set ─────────────────────────────────────────────
y_pred_final = voting_ensemble.predict(X_test)
r2_val   = float(r2_score(y_test, y_pred_final))
mae_val  = float(mean_absolute_error(y_test, y_pred_final))
rmse_val = float(np.sqrt(mean_squared_error(y_test, y_pred_final)))

# ── 3. Feature importances (permutation method) ───────────────────────────────
try:
    perm = permutation_importance(
        best_model, X_test, y_test, n_repeats=10, random_state=42, scoring="r2"
    )
    feat_imp = {
        col: round(float(imp), 4)
        for col, imp in zip(X.columns, perm.importances_mean)
    }
    feat_imp = dict(sorted(feat_imp.items(), key=lambda x: abs(x[1]), reverse=True))
except Exception as e:
    feat_imp = {col: 0.0 for col in X.columns}
    print(f"⚠️  Feature importance non calculée: {e}")

top3 = list(feat_imp.keys())[:3]
primary_cause = f"Lifestyle disruption driven by {top3[0]}" if top3 else "Unknown"

# ── 4. Label qualité du sommeil ───────────────────────────────────────────────
avg_pred = float(np.mean(y_pred_final))
if   avg_pred < 6.0: quality = "INSUFFICIENT"
elif avg_pred < 7.0: quality = "BORDERLINE"
elif avg_pred < 8.5: quality = "ADEQUATE"
else:                quality = "EXCESSIVE"

# ── 5. Construction du JSON d'export ─────────────────────────────────────────
lifestyle_output = {
    "model_name": "lifestyle_routine_cause_classifier",
    "timestamp":  datetime.now(timezone.utc).isoformat(),
    "prediction": {
        "predicted_sleep_hours": round(avg_pred, 2),
        "sleep_quality_label":   quality,
        "routine_trigger":       quality in {"INSUFFICIENT", "BORDERLINE"},
        "confidence":            round(max(0.0, r2_val), 4),
    },
    "trigger_analysis": {
        "primary_cause":        primary_cause,
        "primary_causes":       top3[:2],
        "secondary_causes":     top3[2:],
        "feature_importances":  feat_imp,
    },
    "model_performance": {
        "model_type": "VotingEnsemble (Ridge + SVR + CatBoost + LinearRegression)",
        "r2_score":   round(r2_val,   4),
        "mae_hours":  round(mae_val,  4),
        "rmse_hours": round(rmse_val, 4),
    },
    "all_models_comparison": [
        {
            "model":    row["Model"],
            "r2_test":  round(float(row["R2_Test"]),  4),
            "mae_test": round(float(row["MAE_Test"]), 4),
        }
        for _, row in results_df.iterrows()
    ],
    "dataset_info": {
        "total_rows":    int(len(X_train) + len(X_test)),
        "feature_count": int(len(X.columns)),
        "target_column": "SleepTime",
        "feature_names": list(X.columns),
    },
}

# ── 6. Sauvegarde JSON ────────────────────────────────────────────────────────
with open("lifestyle_model_output.json", "w", encoding="utf-8") as f:
    json.dump(lifestyle_output, f, indent=2, ensure_ascii=False)

print("\n✅ lifestyle_model_output.json sauvegardé")
print(f"   Sommeil prédit    : {avg_pred:.2f}h  [{quality}]")
print(f"   R² du modèle     : {r2_val:.4f}")
print(f"   MAE (heures)      : {mae_val:.4f}")
print(f"   Cause principale  : {primary_cause}")
print(f"\n   Top features:")
for feat, imp in list(feat_imp.items())[:5]:
    bar = "█" * max(1, int(abs(imp) * 15))
    print(f"     {feat:<28}: {imp:+.4f} {bar}")

# ── 7. Téléchargement depuis Colab ───────────────────────────────────────────
from google.colab import files
files.download("lifestyle_model.pkl")
files.download("lifestyle_scaler.pkl")
files.download("lifestyle_model_output.json")
