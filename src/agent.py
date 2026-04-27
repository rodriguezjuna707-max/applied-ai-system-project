import json
import logging
from typing import Dict, List, Tuple

import anthropic

from src.recommender import recommend_songs, load_songs
from src.rag_explainer import explain_with_claude, _get_client

logger = logging.getLogger(__name__)

DEFAULT_PREFS = {
    "genre": "pop",
    "mood": "happy",
    "energy": 0.7,
    "valence": 0.6,
    "danceability": 0.6,
    "acousticness": 0.3,
    "target_popularity": 65,
    "preferred_decade": "2020s",
    "preferred_mood_tag": "",
    "target_instrumentalness": 0.10,
    "target_liveness": 0.15,
}

PARSE_SYSTEM = (
    "You are a music preference parser. "
    "Given a natural language music request, extract structured preferences as JSON. "
    "Return ONLY valid JSON with these keys (use null if unknown): "
    "genre, mood, energy (0.0-1.0), valence (0.0-1.0), danceability (0.0-1.0), "
    "acousticness (0.0-1.0), target_popularity (0-100), preferred_decade "
    "(one of: 1960s/1970s/1980s/1990s/2000s/2010s/2020s), preferred_mood_tag, "
    "target_instrumentalness (0.0-1.0), target_liveness (0.0-1.0). "
    "No explanation, no markdown — raw JSON only."
)

EVAL_SYSTEM = (
    "You are a music recommendation quality evaluator. "
    "Given a user's request and a list of recommended songs, "
    "score the overall match quality from 1 to 10 and provide a one-sentence rationale. "
    "Return ONLY valid JSON: {\"score\": <int>, \"rationale\": \"<string>\"}. "
    "No explanation, no markdown — raw JSON only."
)


def _parse_preferences(query: str) -> Tuple[Dict, str]:
    """Step 1: Use Claude to parse free-text query into structured prefs dict."""
    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=256,
            system=PARSE_SYSTEM,
            messages=[{"role": "user", "content": query}],
        )
        raw = response.content[0].text.strip()
        parsed = json.loads(raw)

        prefs = dict(DEFAULT_PREFS)
        for key, value in parsed.items():
            if value is not None and key in prefs:
                prefs[key] = value

        log_msg = f"AGENT STEP 1 — Parsed preferences: {json.dumps(prefs, indent=None)}"
        logger.info(log_msg)
        return prefs, log_msg

    except (json.JSONDecodeError, anthropic.APIError, Exception) as exc:
        log_msg = f"AGENT STEP 1 — Could not parse query ({type(exc).__name__}), using defaults"
        logger.warning(log_msg)
        return dict(DEFAULT_PREFS), log_msg


def _retrieve(prefs: Dict, songs: List[Dict], k: int = 5) -> Tuple[List, str]:
    """Step 2: Run the scoring retrieval layer."""
    results = recommend_songs(prefs, songs, k=k)
    titles = [s["title"] for s, _, _ in results]
    log_msg = f"AGENT STEP 2 — Retrieved {len(results)} candidates: {titles}"
    logger.info(log_msg)
    return results, log_msg


def _evaluate_match(query: str, results: List) -> Tuple[int, str, str]:
    """Step 3: Ask Claude to score the match quality 1-10."""
    songs_summary = "; ".join(
        f"{s['title']} ({s['genre']}/{s['mood']})" for s, _, _ in results
    )
    eval_prompt = (
        f"User request: {query}\n"
        f"Recommended songs: {songs_summary}\n"
        "Score the match quality 1-10."
    )

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=128,
            system=EVAL_SYSTEM,
            messages=[{"role": "user", "content": eval_prompt}],
        )
        raw = response.content[0].text.strip()
        data = json.loads(raw)
        score = int(data.get("score", 5))
        rationale = data.get("rationale", "No rationale provided.")
        log_msg = f"AGENT STEP 3 — Match quality: {score}/10 — {rationale}"
        logger.info(log_msg)
        return score, rationale, log_msg

    except Exception as exc:
        log_msg = f"AGENT STEP 3 — Evaluation failed ({type(exc).__name__}), assuming score 7"
        logger.warning(log_msg)
        return 7, "Evaluation unavailable.", log_msg


def _refine(prefs: Dict, songs: List[Dict], k: int = 5) -> Tuple[Dict, List, str]:
    """Step 4: Loosen genre constraint and retry retrieval."""
    relaxed = dict(prefs)
    original_genre = relaxed.get("genre", "")
    relaxed["genre"] = ""

    results = recommend_songs(relaxed, songs, k=k)
    titles = [s["title"] for s, _, _ in results]
    log_msg = (
        f"AGENT STEP 4 — Refining: relaxed genre constraint '{original_genre}' → retrying. "
        f"New candidates: {titles}"
    )
    logger.info(log_msg)
    return relaxed, results, log_msg


def run_agent(
    user_query: str,
    songs: List[Dict],
    k: int = 5,
    descriptions_path: str = "data/genre_descriptions.txt",
) -> Dict:
    """
    5-step agentic recommendation workflow.

    Returns a dict with:
      steps          — list of step log strings (observable intermediate output)
      preferences    — the structured prefs used for final retrieval
      recommendations — top-k (song, score, reasons) tuples
      match_quality  — int 1-10
      explanation    — Claude's natural language explanation
    """
    steps: List[str] = []

    # Step 1 — Parse
    prefs, s1 = _parse_preferences(user_query)
    steps.append(s1)

    # Step 2 — Retrieve
    results, s2 = _retrieve(prefs, songs, k=k)
    steps.append(s2)

    # Step 3 — Evaluate
    quality, rationale, s3 = _evaluate_match(user_query, results)
    steps.append(s3)

    # Step 4 — Refine if quality is low
    if quality < 6:
        prefs, results, s4 = _refine(prefs, songs, k=k)
        steps.append(s4)
        quality_note = f"AGENT STEP 4 — Re-evaluated after refinement (previous score: {quality}/10)"
        steps.append(quality_note)

    # Step 5 — Explain
    explanation = explain_with_claude(prefs, results, user_query, descriptions_path)
    steps.append(f"AGENT STEP 5 — Generated explanation ({len(explanation)} chars)")

    return {
        "steps": steps,
        "preferences": prefs,
        "recommendations": results,
        "match_quality": quality,
        "explanation": explanation,
    }
