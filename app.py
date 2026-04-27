import streamlit as st

from src.logger_config import setup_logging
from src.recommender import load_songs, recommend_songs, MAX_SCORE
from src.rag_explainer import explain_with_claude, FALLBACK_PREFIX
from src.agent import run_agent

setup_logging()

DECADE_ORDER = ["1960s", "1970s", "1980s", "1990s", "2000s", "2010s", "2020s"]
DATA_PATH = "data/songs.csv"
GENRE_DESC_PATH = "data/genre_descriptions.txt"


@st.cache_data
def get_songs():
    return load_songs(DATA_PATH)


def get_unique(songs, field):
    return sorted(set(s[field] for s in songs))


def score_bar(score: float, max_score: float = MAX_SCORE, width: int = 20) -> str:
    filled = round((score / max_score) * width)
    return "█" * filled + "░" * (width - filled)


# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="AI Music Recommender", page_icon="🎵", layout="wide")
st.title("🎵 AI Music Recommender")
st.caption("Powered by Claude — RAG + Agentic Workflow")

songs = get_songs()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("Your Preferences")

    mode = st.radio("Mode", ["Standard (RAG)", "Advanced (Agent)"], horizontal=True)
    st.divider()

    if mode == "Advanced (Agent)":
        user_query = st.text_area(
            "Describe what you want to listen to",
            placeholder="e.g. something calm and acoustic for studying late at night",
            height=100,
        )
        find_btn = st.button("Find My Songs", type="primary", use_container_width=True)
    else:
        genres = get_unique(songs, "genre")
        moods = get_unique(songs, "mood")

        genre = st.selectbox("Genre", genres)
        mood = st.selectbox("Mood", moods)
        energy = st.slider("Energy", 0.0, 1.0, 0.7, 0.05)
        valence = st.slider("Valence (positivity)", 0.0, 1.0, 0.6, 0.05)
        danceability = st.slider("Danceability", 0.0, 1.0, 0.6, 0.05)
        acousticness = st.slider("Acousticness", 0.0, 1.0, 0.3, 0.05)
        decade = st.selectbox("Preferred Decade", DECADE_ORDER, index=6)
        popularity = st.slider("Target Popularity (0–100)", 0, 100, 70)

        find_btn = st.button("Find My Songs", type="primary", use_container_width=True)

# ── Main panel ────────────────────────────────────────────────────────────────
if find_btn:
    if mode == "Advanced (Agent)":
        if not user_query.strip():
            st.warning("Please describe what you want to listen to.")
            st.stop()

        with st.spinner("Agent is thinking through your request..."):
            result = run_agent(user_query, songs, descriptions_path=GENRE_DESC_PATH)

        st.subheader("Agent Reasoning Steps")
        with st.expander("Show agent steps", expanded=False):
            for step in result["steps"]:
                st.code(step, language=None)

        top_songs = result["recommendations"]
        explanation = result["explanation"]
        quality = result["match_quality"]
        st.info(f"Match quality score: **{quality}/10**")

    else:
        user_prefs = {
            "genre": genre,
            "mood": mood,
            "energy": energy,
            "valence": valence,
            "danceability": danceability,
            "acousticness": acousticness,
            "target_popularity": popularity,
            "preferred_decade": decade,
            "preferred_mood_tag": "",
            "target_instrumentalness": 0.10,
            "target_liveness": 0.15,
        }

        prefs_key = str(user_prefs)
        if st.session_state.get("last_prefs") == prefs_key and "last_result" in st.session_state:
            top_songs = st.session_state["last_result"]["songs"]
            explanation = st.session_state["last_result"]["explanation"]
        else:
            top_songs = recommend_songs(user_prefs, songs, k=5)
            with st.spinner("Claude is personalizing your explanation..."):
                explanation = explain_with_claude(
                    user_prefs, top_songs, descriptions_path=GENRE_DESC_PATH
                )
            st.session_state["last_prefs"] = prefs_key
            st.session_state["last_result"] = {"songs": top_songs, "explanation": explanation}

    # ── Song cards ────────────────────────────────────────────────────────────
    st.subheader("Your Top Recommendations")
    cols = st.columns(min(len(top_songs), 3))
    for i, (song, score, reasons) in enumerate(top_songs):
        col = cols[i % 3]
        with col:
            st.markdown(f"**#{i+1} {song['title']}**")
            st.markdown(f"*{song['artist']}*")
            st.markdown(
                f"`{song['genre']}` · `{song['mood']}` · `{song.get('mood_tag', '')}`"
            )
            st.markdown(
                f"Decade: {song.get('release_decade','?')} · Pop: {song.get('popularity','?')}"
            )
            bar = score_bar(score)
            st.markdown(f"`{bar}` {score:.2f}/{MAX_SCORE:.2f}")
            with st.expander("Why matched"):
                for r in reasons[:5]:
                    st.markdown(f"- {r}")
            st.divider()

    # ── Claude explanation ────────────────────────────────────────────────────
    st.subheader("Your Personalized Explanation")
    if explanation.startswith(FALLBACK_PREFIX):
        st.warning(explanation.replace(FALLBACK_PREFIX, "").strip())
    else:
        st.info(explanation)
