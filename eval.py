"""
Evaluation harness for the AI Music Recommender.

Runs 8 predefined test cases against the retrieval layer (no API calls required)
and prints a pass/fail summary with scores.

Usage:
    python eval.py
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from src.recommender import load_songs, recommend_songs, MAX_SCORE

SONGS = load_songs("data/songs.csv")

# ---------------------------------------------------------------------------
# Test cases: (label, user_prefs, assertion_fn, description)
# ---------------------------------------------------------------------------

TEST_CASES = [
    {
        "label": "HIGH_ENERGY_POP",
        "prefs": {
            "genre": "pop", "mood": "happy", "energy": 0.9, "valence": 0.85,
            "danceability": 0.88, "acousticness": 0.05, "target_popularity": 85,
            "preferred_decade": "2020s", "preferred_mood_tag": "euphoric",
            "target_instrumentalness": 0.03, "target_liveness": 0.10,
        },
        "check": lambda results: (
            results[0][0]["genre"] == "pop" or results[0][0]["mood"] == "happy"
        ),
        "description": "Top result should be pop or happy",
    },
    {
        "label": "CHILL_LOFI",
        "prefs": {
            "genre": "lofi", "mood": "chill", "energy": 0.3, "valence": 0.45,
            "danceability": 0.35, "acousticness": 0.70, "target_popularity": 55,
            "preferred_decade": "2020s", "preferred_mood_tag": "serene",
            "target_instrumentalness": 0.85, "target_liveness": 0.06,
        },
        "check": lambda results: results[0][0]["energy"] < 0.5,
        "description": "Top result energy should be < 0.5 (chill/low energy)",
    },
    {
        "label": "DEEP_INTENSE_ROCK",
        "prefs": {
            "genre": "rock", "mood": "intense", "energy": 0.92, "valence": 0.30,
            "danceability": 0.40, "acousticness": 0.08, "target_popularity": 72,
            "preferred_decade": "2010s", "preferred_mood_tag": "gritty",
            "target_instrumentalness": 0.15, "target_liveness": 0.25,
        },
        "check": lambda results: (
            results[0][0]["genre"] == "rock" or results[0][0]["mood"] == "intense"
        ),
        "description": "Top result should be rock or intense",
    },
    {
        "label": "RARE_GENRE_LOW_SCORE",
        "prefs": {
            "genre": "bossa nova", "mood": "chill", "energy": 0.35, "valence": 0.60,
            "danceability": 0.50, "acousticness": 0.65, "target_popularity": 40,
            "preferred_decade": "1990s", "preferred_mood_tag": "romantic",
            "target_instrumentalness": 0.50, "target_liveness": 0.55,
        },
        "check": lambda results: results[0][1] < 4.5,
        "description": "Top score should be < 4.5 (no perfect match for bossa nova)",
    },
    {
        "label": "PERFECTLY_AVERAGE_RETURNS_5",
        "prefs": {
            "genre": "jazz", "mood": "relaxed", "energy": 0.50, "valence": 0.50,
            "danceability": 0.50, "acousticness": 0.50, "target_popularity": 50,
            "preferred_decade": "2010s", "preferred_mood_tag": "",
            "target_instrumentalness": 0.50, "target_liveness": 0.50,
        },
        "check": lambda results: len(results) == 5,
        "description": "Should return 5 results even with all-neutral prefs",
    },
    {
        "label": "EMPTY_QUERY_GUARDRAIL",
        "prefs": {
            "genre": "", "mood": "", "energy": 0.5, "valence": 0.5,
            "danceability": 0.5, "acousticness": 0.5, "target_popularity": 50,
            "preferred_decade": "", "preferred_mood_tag": "",
            "target_instrumentalness": 0.5, "target_liveness": 0.5,
        },
        "check": lambda results: len(results) >= 0,
        "description": "Empty/blank prefs should not crash — returns any results",
    },
    {
        "label": "ACOUSTIC_METALHEAD_CONTRADICTORY",
        "prefs": {
            "genre": "metal", "mood": "intense", "energy": 0.95, "valence": 0.20,
            "danceability": 0.30, "acousticness": 1.00, "target_popularity": 80,
            "preferred_decade": "2010s", "preferred_mood_tag": "aggressive",
            "target_instrumentalness": 0.20, "target_liveness": 0.30,
        },
        "check": lambda results: len(results) == 5 and results[0][1] > 0,
        "description": "Contradictory prefs still produce 5 results with positive scores",
    },
    {
        "label": "SCORE_IN_VALID_RANGE",
        "prefs": {
            "genre": "pop", "mood": "happy", "energy": 0.8, "valence": 0.8,
            "danceability": 0.7, "acousticness": 0.1, "target_popularity": 75,
            "preferred_decade": "2020s", "preferred_mood_tag": "",
            "target_instrumentalness": 0.05, "target_liveness": 0.10,
        },
        "check": lambda results: all(0 <= score <= MAX_SCORE for _, score, _ in results),
        "description": f"All scores should be between 0 and MAX_SCORE ({MAX_SCORE:.2f})",
    },
]


def run_eval():
    print("=" * 64)
    print("  AI MUSIC RECOMMENDER — EVALUATION HARNESS")
    print("=" * 64)
    print(f"  Songs in catalog: {len(SONGS)}  |  MAX_SCORE: {MAX_SCORE:.2f}\n")

    passed = 0
    failed = 0
    failures = []

    for tc in TEST_CASES:
        try:
            results = recommend_songs(tc["prefs"], SONGS, k=5)
            ok = tc["check"](results)
        except Exception as exc:
            ok = False
            failures.append((tc["label"], tc["description"], f"EXCEPTION: {exc}", None))
            print(f"  [FAIL] {tc['label']}: {tc['description']}")
            print(f"         Exception: {exc}")
            failed += 1
            continue

        status = "PASS" if ok else "FAIL"
        top = results[0] if results else None
        top_info = (
            f"{top[0]['title']} ({top[0]['genre']}/{top[0]['mood']}) score={top[1]:.2f}"
            if top else "no results"
        )

        print(f"  [{status}] {tc['label']}")
        print(f"         Check: {tc['description']}")
        print(f"         Top result: {top_info}")

        if ok:
            passed += 1
        else:
            failed += 1
            failures.append((tc["label"], tc["description"], top_info, results))

    print("\n" + "=" * 64)
    print(f"  SUMMARY: Passed {passed}/{len(TEST_CASES)}  |  Failed {failed}/{len(TEST_CASES)}")
    pct = (passed / len(TEST_CASES)) * 100
    print(f"  Pass rate: {pct:.1f}%")

    if failures:
        print("\n  FAILURES:")
        for label, desc, actual, _ in failures:
            print(f"    - {label}: {desc}")
            print(f"      Actual: {actual}")

    print("=" * 64)
    return passed, failed


if __name__ == "__main__":
    passed, failed = run_eval()
    sys.exit(0 if failed == 0 else 1)
