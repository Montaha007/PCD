# Sleep & Mental Wellness — Multi-Agent System
### Rapport Chapitre 5 — Modeling

---

## Architecture (§5.1 System Architectural Design)

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
INPUT  (§3.1 Datasets)
  Sleep log data       →  §5.2.1 Sleep Model
  Lifestyle log data   →  §5.2.2 Lifestyle Model
  Journal entries      →  §5.2.3 NLP Model
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
§5.2 MODEL LAYER
  §5.2.1 Sleep Model     — Binary Classifier (Insomnia: yes/no)
                           + Qdrant kNN confirmation (§5.1.3.1)
  §5.2.2 Lifestyle Model — Routine Cause Classifier (VotingEnsemble)
                           Feature importances → cause identification
  §5.2.3 NLP Model       — Sentiment + Cause Extraction
                           Qdrant semantic search (§5.1.3.1)
                           + Neo4j graph traversal (§5.1.3.2)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
§5.3 AGENT LAYER (CrewAI — §5.4)
  Agent 1: Correlation Agent (§5.3.1)
    §5.3.1.1 Model Output Aggregation
    §5.3.1.2 Confidence Weighting
    §5.3.1.3 Conflict Detection
    §5.3.1.4 Unified Insomnia Profile Generation
        ↓ (§5.4.3 data flow via CrewAI context)
  Agent 2: Reasoning Agent (§5.3.2)
    §5.3.2.1 Rule-Based Reasoning (3P Model + DSM-5 + ICSD-3)
    §5.3.2.2 Root Cause Ranking (+ Neo4j graph evidence §5.1.3.2)
    §5.3.2.3 Edge Case Detection
        ↓ (§5.4.3 data flow via CrewAI context)
  Agent 3: Recommendation Agent (§5.3.3)
    §5.3.3.1 Personalized Recommendation (LLM role §5.1.3.3)
    §5.3.3.2 Sleep Hygiene Recommendations
    §5.3.3.3 CBT-I Suggestions
    §5.3.3.4 Lifestyle Adjustment Recommendations
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
§5.5 FINAL SYSTEM OUTPUT
  §5.5.1 Diagnosis Generation
  §5.5.2 Confidence Estimation
  §5.5.3 Cause Breakdown
  §5.5.4 Action Plan Generation
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

---

## Project Structure

```
sleep_wellness_multiagent/
│
├── inference/                   §5.2 Model Layer
│   ├── sleep_inference.py       §5.2.1 Sleep Model (+ Qdrant §5.1.3.1)
│   ├── lifestyle_inference.py   §5.2.2 Lifestyle Model
│   └── nlp_inference.py         §5.2.3 NLP Model (Qdrant §5.1.3.1 + Neo4j §5.1.3.2)
│
├── agents/                      §5.3 Agent Layer
│   ├── correlation_agent.py     §5.3.1 Agent 1
│   ├── reasoning_agent.py       §5.3.2 Agent 2
│   └── recommendation_agent.py  §5.3.3 Agent 3
│
├── tasks/                       §5.4 Orchestration
│   ├── correlation_task.py      §5.4.2 Task 1
│   ├── reasoning_task.py        §5.4.2 Task 2
│   └── recommendation_task.py   §5.4.2 Task 3
│
├── models/                      §5.2 pkl files (from Colab)
│   └── README.md
│
├── notebook_exports/            Export cells for Colab notebooks
│   ├── export_insomnia_pipeline.py
│   ├── export_lifestyle_model.py
│   └── export_nlp_graphrag.py
│
├── crew.py                      §5.4 CrewAI Orchestration
├── model_loader.py              §5.2 → §5.3 bridge
├── main.py                      Entry point
├── config.py                    §7.1.2 Configuration
├── requirements.txt             §7.1.2.2 Dependencies
└── .env.example                 §7.1.2.3 Credentials template
```

---

## Quick Start (§7.1 Environment and Working Tools)

```bash
# 1. Install dependencies (§7.1.2.2)
pip install -r requirements.txt

# 2. Configure credentials (§7.1.2.3)
cp .env.example .env
# Fill in: OPENAI_API_KEY, QDRANT_URL, QDRANT_API_KEY, NEO4J_URI, NEO4J_USERNAME, NEO4J_PASSWORD

# 3. Export models from Colab (§5.2 Model Layer)
#    → Copy notebook_exports/export_insomnia_pipeline.py to last cell of insomnia_combined_pipeline.ipynb
#    → Copy notebook_exports/export_lifestyle_model.py   to last cell of Data_Vis.ipynb
#    → Copy notebook_exports/export_nlp_graphrag.py      to last cell of neo4j_graphrag.ipynb
#    → Place downloaded .pkl files in models/

# 4. Run the pipeline
python main.py
```

---

## Backend Integration

Your colleague's backend only needs to call one function:

```python
from main import analyze_user

user_data = {
    "user_id": "user-123",
    "sleep_features": {
        "Age": 28, "Gender": 1, "BMI": 23.5,
        "SleepDuration": 5.2, "QualityOfSleep": 3,
        "HeartRate": 78, "DailySteps": 4200,
        "PhysicalActivity": 2
    },
    "lifestyle_features": {
        "WorkoutTime": 0.5, "ReadingTime": 0.3,
        "PhoneTime": 4.2, "WorkHours": 10.5,
        "CaffeineIntake": 380, "RelaxationTime": 0.4
    },
    "journal_text": "I've been feeling really anxious lately..."
}

result = analyze_user(user_data)
# result["final_output"] → send to frontend dashboard
```

### Output structure (§5.5 Final System Output)
```json
{
  "diagnosis":        { "insomnia_confirmed": true, "confidence": 0.78 },
  "cause_breakdown":  [ { "rank": "PRIMARY", "cause": "...", "clinical_weight": 0.75 } ],
  "action_plan":      { "short_term": { "actions": [...] }, "long_term": { "phases": [...] } },
  "plan_summary":     "Your primary challenge is..."
}
```

---

## Knowledge Infrastructure (§5.1.3)

| Component | Role | Used in |
|-----------|------|---------|
| **Qdrant** (§5.1.3.1) | Shared vector store | §5.2.1 Sleep Model + §5.2.3 NLP Model |
| **Neo4j** (§5.1.3.2) | Causal graph knowledge base | §5.2.3 NLP inference + §5.3.2.2 Reasoning evidence |
| **LLM GPT-4o** (§5.1.3.3) | Powers all 3 agents | §5.3.1 + §5.3.2 + §5.3.3 |

**Qdrant** is already populated from your notebooks (`PCD_Sleep_Disorder+Semantic`).
**Neo4j** is already built from `neo4j_graphrag.ipynb`.
No re-indexing needed — just set credentials in `.env`.
