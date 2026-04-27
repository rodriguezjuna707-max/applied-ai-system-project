"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

try:
    from recommender import load_songs, recommend_songs, MAX_SCORE   # python src/main.py
except ImportError:
    from src.recommender import load_songs, recommend_songs, MAX_SCORE  # python -m src.main


# ---------------------------------------------------------------------------
# Named user preference profiles
#
# Each dict maps feature names to the user's target values.
# Categorical fields (genre, mood, preferred_decade, preferred_mood_tag) use
# exact (or adjacency-decay) matching.
# Numeric fields (0.0–1.0) use proximity scoring.
#
# New advanced keys (Challenge 1):
#   target_popularity      — preferred popularity level (0–100)
#   preferred_decade       — era the user gravitates toward
#   preferred_mood_tag     — detailed mood tag (empty string = don't care)
#   target_instrumentalness — 0 = vocal-heavy, 1 = fully instrumental
#   target_liveness        — 0 = studio-clean, 1 = live-concert feel
# ---------------------------------------------------------------------------

HIGH_ENERGY_POP = {
    "genre":                    "pop",
    "mood":                     "happy",
    "energy":                   0.90,
    "valence":                  0.85,
    "danceability":             0.88,
    "acousticness":             0.05,
    # new
    "target_popularity":        85,       # wants chart-toppers
    "preferred_decade":         "2020s",  # current era
    "preferred_mood_tag":       "euphoric",
    "target_instrumentalness":  0.03,     # full vocals
    "target_liveness":          0.10,     # polished studio sound
}

CHILL_LOFI = {
    "genre":                    "lofi",
    "mood":                     "chill",
    "energy":                   0.30,
    "valence":                  0.45,
    "danceability":             0.35,
    "acousticness":             0.70,
    # new
    "target_popularity":        55,       # prefers underground / niche
    "preferred_decade":         "2020s",
    "preferred_mood_tag":       "serene",
    "target_instrumentalness":  0.85,     # mostly instrumental
    "target_liveness":          0.06,     # very clean recording
}

DEEP_INTENSE_ROCK = {
    "genre":                    "rock",
    "mood":                     "intense",
    "energy":                   0.92,
    "valence":                  0.30,
    "danceability":             0.40,
    "acousticness":             0.08,
    # new
    "target_popularity":        72,       # well-known but not mainstream pop
    "preferred_decade":         "2010s",
    "preferred_mood_tag":       "gritty",
    "target_instrumentalness":  0.15,     # mostly vocals with heavy guitar
    "target_liveness":          0.25,     # slight live rawness is welcome
}

# ---------------------------------------------------------------------------
# Adversarial / edge-case profiles
# ---------------------------------------------------------------------------

# EDGE 1 — Conflicting categorical + numeric intent
CONFLICTING_ENERGY_SAD = {
    "genre":                    "indie",
    "mood":                     "sad",
    "energy":                   0.90,
    "valence":                  0.15,
    "danceability":             0.50,
    "acousticness":             0.40,
    # new
    "target_popularity":        60,
    "preferred_decade":         "2010s",
    "preferred_mood_tag":       "bittersweet",
    "target_instrumentalness":  0.20,
    "target_liveness":          0.20,
}

# EDGE 2 — Rare genre with no catalog representative
RARE_GENRE = {
    "genre":                    "bossa nova",
    "mood":                     "chill",
    "energy":                   0.35,
    "valence":                  0.60,
    "danceability":             0.50,
    "acousticness":             0.65,
    # new
    "target_popularity":        40,       # niche listener
    "preferred_decade":         "1990s",  # older era — unlikely to match 2020s catalog
    "preferred_mood_tag":       "romantic",
    "target_instrumentalness":  0.50,
    "target_liveness":          0.55,     # appreciates live recordings
}

# EDGE 3 — All numeric targets at midpoint — zero discrimination power
PERFECTLY_AVERAGE = {
    "genre":                    "jazz",
    "mood":                     "relaxed",
    "energy":                   0.50,
    "valence":                  0.50,
    "danceability":             0.50,
    "acousticness":             0.50,
    # new — also at midpoints
    "target_popularity":        50,
    "preferred_decade":         "2010s",
    "preferred_mood_tag":       "",        # empty = don't care about detailed tag
    "target_instrumentalness":  0.50,
    "target_liveness":          0.50,
}

# EDGE 4 — Max acoustic desire paired with electric genre
ACOUSTIC_METALHEAD = {
    "genre":                    "metal",
    "mood":                     "intense",
    "energy":                   0.95,
    "valence":                  0.20,
    "danceability":             0.30,
    "acousticness":             1.00,
    # new
    "target_popularity":        80,
    "preferred_decade":         "2010s",
    "preferred_mood_tag":       "aggressive",
    "target_instrumentalness":  0.20,
    "target_liveness":          0.30,
}


# ---------------------------------------------------------------------------
# Display helper
# ---------------------------------------------------------------------------

def print_recommendations(user_prefs: dict, songs: list, label: str, k: int = 5) -> None:
    recommendations = recommend_songs(user_prefs, songs, k=k)

    width = 64
    print("\n" + "=" * width)
    print(f" {label} ".center(width))
    print(
        f" {user_prefs['genre']} / {user_prefs['mood']} / "
        f"energy {user_prefs['energy']} / {user_prefs.get('preferred_decade','')} ".center(width)
    )
    print("=" * width)

    for rank, (song, score, reasons) in enumerate(recommendations, start=1):
        bar_filled = round((score / MAX_SCORE) * 20)
        bar = "#" * bar_filled + "-" * (20 - bar_filled)

        print(f"\n  #{rank}  {song['title']} by {song['artist']}")
        print(f"       [{bar}] {score:.2f} / {MAX_SCORE:.2f}")
        print(
            f"       Genre: {song['genre']}  |  Mood: {song['mood']}  "
            f"|  Tag: {song.get('mood_tag','')}  "
            f"|  Decade: {song.get('release_decade','')}  "
            f"|  Pop: {song.get('popularity','?')}"
        )
        print("       Why recommended:")
        for reason in reasons:
            print(f"         - {reason}")

    print("\n" + "=" * width)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main() -> None:
    songs = load_songs("data/songs.csv")

    # --- Named profiles ---
    print_recommendations(HIGH_ENERGY_POP,   songs, "HIGH-ENERGY POP")
    print_recommendations(CHILL_LOFI,        songs, "CHILL LOFI")
    print_recommendations(DEEP_INTENSE_ROCK, songs, "DEEP INTENSE ROCK")

    # --- Adversarial / edge-case profiles ---
    print("\n\n" + "#" * 64)
    print("  ADVERSARIAL / EDGE-CASE PROFILES".center(64))
    print("#" * 64)

    print_recommendations(CONFLICTING_ENERGY_SAD, songs, "EDGE 1 — Conflicting: high energy + sad mood")
    print_recommendations(RARE_GENRE,             songs, "EDGE 2 — Rare genre (bossa nova) + 1990s")
    print_recommendations(PERFECTLY_AVERAGE,      songs, "EDGE 3 — All numerics at midpoint")
    print_recommendations(ACOUSTIC_METALHEAD,     songs, "EDGE 4 — Acoustic metalhead (contradictory)")


if __name__ == "__main__":
    main()
