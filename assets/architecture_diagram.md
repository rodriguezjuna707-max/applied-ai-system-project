# System Architecture Diagram

This diagram reflects the actual upgraded implementation.

```mermaid
flowchart TD
    A([User Input\nSidebar prefs OR free-text query]) --> B[app.py\nStreamlit UI]

    B -->|Standard Mode| C[recommend_songs\nsrc/recommender.py]
    B -->|Advanced Mode| D[run_agent\nsrc/agent.py]

    D --> D1[Step 1: Claude parses\nfree-text → structured prefs JSON]
    D1 --> D2[Step 2: recommend_songs\nretrieve top-5 candidates]
    D2 --> D3[Step 3: Claude evaluates\nmatch quality score 1-10]
    D3 -->|score >= 6| D5[Step 5: explain_with_claude]
    D3 -->|score < 6| D4[Step 4: Relax genre constraint\nretry retrieval]
    D4 --> D5

    C --> E[explain_with_claude\nsrc/rag_explainer.py]
    D5 --> E

    E --> R1[(songs.csv\nRetrieval Source 1)]
    E --> R2[(genre_descriptions.txt\nRetrieval Source 2)]
    R1 --> E
    R2 --> E

    E --> F[Claude API\nclaude-sonnet-4-6\nGeneration Layer]
    F -->|API error| G[Rule-based fallback\nreasons list]

    F --> H[Song Cards +\nPersonalized Explanation]
    G --> H

    B --> L[recommender.log\nAudit trail]
    E --> L
    D --> L

    subgraph Reliability
        T[pytest tests/\n18 tests, mocked API]
        EV[eval.py\n8 predefined inputs\npass/fail summary]
        GR[Guardrails\nempty songs / short response\nAPI error / invalid k]
    end
```

## Components

| Component | File | Role |
|---|---|---|
| Streamlit UI | `app.py` | Main entry point, Standard + Advanced modes |
| Recommender | `src/recommender.py` | Scoring engine (MAX_SCORE 6.80), data loading |
| RAG Explainer | `src/rag_explainer.py` | Multi-source retrieval + Claude generation |
| Agent | `src/agent.py` | 5-step agentic workflow with observable steps |
| Logger | `src/logger_config.py` | File + console logging |
| Song Catalog | `data/songs.csv` | 18-song retrieval source |
| Genre Knowledge | `data/genre_descriptions.txt` | Second retrieval source for Claude context |
| Test Suite | `tests/` | 18 tests, all API calls mocked |
| Eval Harness | `eval.py` | 8 test cases, no API key required |
