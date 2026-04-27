import math
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass, field

@dataclass
class Song:
    """
    Represents a song and its attributes.
    Required by tests/test_recommender.py
    """
    id: int
    title: str
    artist: str
    genre: str
    mood: str
    energy: float
    tempo_bpm: float
    valence: float
    danceability: float
    acousticness: float
    # ── 5 new advanced attributes ──────────────────────────────────────────────
    popularity: float           # 0–100  streaming popularity score
    release_decade: str         # e.g. "2010s"  era of the track
    mood_tag: str               # detailed tag: euphoric / serene / gritty / …
    instrumentalness: float     # 0.0–1.0  fraction without vocals
    liveness: float             # 0.0–1.0  live-recording feel


@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    likes_acoustic: bool
    # ── 5 new advanced preference fields ──────────────────────────────────────
    target_popularity: float = 70.0     # preferred popularity level (0–100)
    preferred_decade: str = "2020s"     # era the user gravitates toward
    preferred_mood_tag: str = ""        # detailed mood tag (empty = don't care)
    target_instrumentalness: float = 0.10   # 0 = lots of vocals, 1 = fully instrumental
    target_liveness: float = 0.15       # 0 = studio-clean, 1 = live-concert feel


class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        # TODO: Implement recommendation logic
        return self.songs[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        # TODO: Implement explanation logic
        return "Explanation placeholder"


# ---------------------------------------------------------------------------
# Scoring weights — updated to include 5 new features.
#
# Original features (sum = 5.00):
#   genre 1.00 | mood 1.00 | energy 2.00 | valence 0.60
#   danceability 0.25 | acousticness 0.15
#
# New features (sum = 1.80):
#   popularity 0.50 | release_decade 0.40 | mood_tag 0.60
#   instrumentalness 0.20 | liveness 0.10
#
# New MAX_SCORE = 6.80
# ---------------------------------------------------------------------------

POINTS = {
    # ── Original features ─────────────────────────────────────────────────────
    "genre":             1.00,   # hard stylistic boundary
    "mood":              1.00,   # broad emotional intent
    "energy":            2.00,   # widest catalog spread — most discriminating
    "valence":           0.60,   # secondary emotional coloring
    "danceability":      0.25,   # minor refinement
    "acousticness":      0.15,   # minor refinement
    # ── New advanced features ─────────────────────────────────────────────────
    "popularity":        0.50,   # square-root curve — rewards popular, not blindly
    "release_decade":    0.40,   # full for exact era, half for adjacent decade
    "mood_tag":          0.60,   # exact-match bonus over broad mood
    "instrumentalness":  0.20,   # proximity — vocals vs. instrumental preference
    "liveness":          0.10,   # proximity — studio vs. live preference
}

MAX_SCORE = sum(POINTS.values())  # 6.80

# Ordered list of decades for adjacency scoring
DECADE_ORDER = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]


# ---------------------------------------------------------------------------
# load_songs
# ---------------------------------------------------------------------------

def load_songs(csv_path: str) -> List[Dict]:
    """Parse songs.csv and return a list of dicts with numeric fields cast appropriately."""
    import csv
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # original numeric fields
            row["id"]               = int(row["id"])
            row["energy"]           = float(row["energy"])
            row["tempo_bpm"]        = float(row["tempo_bpm"])
            row["valence"]          = float(row["valence"])
            row["danceability"]     = float(row["danceability"])
            row["acousticness"]     = float(row["acousticness"])
            # new numeric fields
            row["popularity"]       = float(row["popularity"])
            row["instrumentalness"] = float(row["instrumentalness"])
            row["liveness"]         = float(row["liveness"])
            # new string fields stay as-is: release_decade, mood_tag
            songs.append(row)
    return songs


# ---------------------------------------------------------------------------
# score_song  — all scoring math documented inline
# ---------------------------------------------------------------------------

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, List[str]]:
    """
    Score one song against user preferences (max 6.80) and return (score, reasons).

    Scoring rules:
      Categorical (binary exact match):
        genre, mood, mood_tag, release_decade (with adjacency decay)
      Numeric (proximity: pts × (1 − |song − user|)):
        energy, valence, danceability, acousticness, instrumentalness, liveness
      Non-linear numeric:
        popularity — square-root curve: pts × √(popularity/100)
          rewards popular tracks but compresses the gap between 80 and 100.
      Decade adjacency decay:
        full pts for exact decade, 50 % for ±1 decade, 0 for anything further.
    """
    reasons: List[str] = []

    # ── Categorical: genre ────────────────────────────────────────────────────
    genre_pts = POINTS["genre"] if song["genre"] == user_prefs.get("genre") else 0.0
    if genre_pts:
        reasons.append(f"genre match ({song['genre']}) (+{genre_pts:.2f})")

    # ── Categorical: mood ─────────────────────────────────────────────────────
    mood_pts = POINTS["mood"] if song["mood"] == user_prefs.get("mood") else 0.0
    if mood_pts:
        reasons.append(f"mood match ({song['mood']}) (+{mood_pts:.2f})")

    # ── Categorical: mood_tag (detailed) — bonus on top of broad mood ─────────
    mood_tag_pts = 0.0
    preferred_tag = user_prefs.get("preferred_mood_tag", "")
    if preferred_tag and song.get("mood_tag") == preferred_tag:
        mood_tag_pts = POINTS["mood_tag"]
        reasons.append(f"mood tag match ({song['mood_tag']}) (+{mood_tag_pts:.2f})")

    # ── Categorical: release_decade with adjacency decay ─────────────────────
    #   Distance 0  → 100 % of points
    #   Distance 1  →  50 % of points  (adjacent decade, e.g. 2010s vs 2020s)
    #   Distance 2+ →   0 points
    decade_pts = 0.0
    preferred_decade = user_prefs.get("preferred_decade", "")
    song_decade = song.get("release_decade", "")
    if preferred_decade and song_decade:
        try:
            user_idx = DECADE_ORDER.index(preferred_decade)
            song_idx = DECADE_ORDER.index(song_decade)
            distance = abs(user_idx - song_idx)
            if distance == 0:
                decade_pts = POINTS["release_decade"]
                reasons.append(f"decade match ({song_decade}) (+{decade_pts:.2f})")
            elif distance == 1:
                decade_pts = POINTS["release_decade"] * 0.50
                reasons.append(
                    f"adjacent decade ({song_decade} ~= {preferred_decade}) (+{decade_pts:.2f})"
                )
        except ValueError:
            pass  # unknown decade string — skip silently

    # ── Non-linear numeric: popularity — square-root compression ─────────────
    #   Formula: pts × √(popularity / 100)
    #   At pop=100 → full pts; pop=64 → 0.8×pts; pop=25 → 0.5×pts; pop=0 → 0
    #   Why sqrt? Streaming hits are mostly over 60; this ensures moderate
    #   popularity (60-75) still earns ~80% of the reward rather than being
    #   dwarfed by chart-toppers.
    raw_pop = song.get("popularity", 50.0)
    popularity_pts = POINTS["popularity"] * math.sqrt(raw_pop / 100.0)
    reasons.append(
        f"popularity {raw_pop:.0f}/100 -> sqrt score (+{popularity_pts:.2f})"
    )

    # ── Numeric proximity: energy ─────────────────────────────────────────────
    energy_pts = POINTS["energy"] * (1.0 - abs(song["energy"] - user_prefs.get("energy", 0.5)))
    reasons.append(
        f"energy {song['energy']:.2f} vs target {user_prefs.get('energy', 0.5):.2f} (+{energy_pts:.2f})"
    )

    # ── Numeric proximity: valence ────────────────────────────────────────────
    valence_pts = POINTS["valence"] * (1.0 - abs(song["valence"] - user_prefs.get("valence", 0.5)))
    reasons.append(
        f"valence {song['valence']:.2f} vs target {user_prefs.get('valence', 0.5):.2f} (+{valence_pts:.2f})"
    )

    # ── Numeric proximity: danceability ──────────────────────────────────────
    danceability_pts = POINTS["danceability"] * (
        1.0 - abs(song["danceability"] - user_prefs.get("danceability", 0.5))
    )
    reasons.append(
        f"danceability {song['danceability']:.2f} vs target {user_prefs.get('danceability', 0.5):.2f} (+{danceability_pts:.2f})"
    )

    # ── Numeric proximity: acousticness ──────────────────────────────────────
    acousticness_pts = POINTS["acousticness"] * (
        1.0 - abs(song["acousticness"] - user_prefs.get("acousticness", 0.5))
    )
    reasons.append(
        f"acousticness {song['acousticness']:.2f} vs target {user_prefs.get('acousticness', 0.5):.2f} (+{acousticness_pts:.2f})"
    )

    # ── Numeric proximity: instrumentalness ──────────────────────────────────
    instrumentalness_pts = POINTS["instrumentalness"] * (
        1.0 - abs(song.get("instrumentalness", 0.5) - user_prefs.get("target_instrumentalness", 0.5))
    )
    reasons.append(
        f"instrumentalness {song.get('instrumentalness', 0.5):.2f} vs target "
        f"{user_prefs.get('target_instrumentalness', 0.5):.2f} (+{instrumentalness_pts:.2f})"
    )

    # ── Numeric proximity: liveness ───────────────────────────────────────────
    liveness_pts = POINTS["liveness"] * (
        1.0 - abs(song.get("liveness", 0.5) - user_prefs.get("target_liveness", 0.5))
    )
    reasons.append(
        f"liveness {song.get('liveness', 0.5):.2f} vs target "
        f"{user_prefs.get('target_liveness', 0.5):.2f} (+{liveness_pts:.2f})"
    )

    score = (
        genre_pts + mood_pts + mood_tag_pts + decade_pts
        + popularity_pts
        + energy_pts + valence_pts + danceability_pts + acousticness_pts
        + instrumentalness_pts + liveness_pts
    )
    return score, reasons


# ---------------------------------------------------------------------------
# recommend_songs
# ---------------------------------------------------------------------------

def recommend_songs(
    user_prefs: Dict, songs: List[Dict], k: int = 5
) -> List[Tuple[Dict, float, List[str]]]:
    """Score every song, sort descending, and return the top k."""
    scored = [
        (song, score, reasons)
        for song in songs
        for score, reasons in [score_song(user_prefs, song)]
    ]
    return sorted(scored, key=lambda x: x[1], reverse=True)[:k]
