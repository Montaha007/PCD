# models/  — §5.2 Model Layer pkl files

Place your trained models here (downloaded from Colab with `files.download()`).

## Files needed

| File | Source notebook | Export command |
|------|----------------|----------------|
| `sleep_classifier.pkl` | `insomnia_combined_pipeline.ipynb` | `joblib.dump(best_model, "sleep_classifier.pkl")` |
| `sleep_scaler.pkl` | `insomnia_combined_pipeline.ipynb` | `joblib.dump(scaler, "sleep_scaler.pkl")` |
| `lifestyle_model.pkl` | `Data_Vis.ipynb` | `joblib.dump(voting_ensemble, "lifestyle_model.pkl")` |
| `lifestyle_scaler.pkl` | `Data_Vis.ipynb` | `joblib.dump(scaler, "lifestyle_scaler.pkl")` |

## NLP model (§5.2.3) — no pkl needed
The NLP model connects directly to:
- **Qdrant Cloud** — collection `PCD_Sleep_Disorder+Semantic` already populated (§5.1.3.1)
- **Neo4j Aura** — graph already built via `neo4j_graphrag.ipynb` (§5.1.3.2)
Set credentials in `.env` file.
