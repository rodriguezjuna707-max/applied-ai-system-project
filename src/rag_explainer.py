import logging
import os
from typing import Dict, List, Tuple

import anthropic

logger = logging.getLogger(__name__)

_CLIENT: anthropic.Anthropic | None = None
_GENRE_CACHE: Dict[str, str] = {}

FALLBACK_PREFIX = "[FALLBACK]"


def _get_client() -> anthropic.Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = anthropic.Anthropic()
    return _CLIENT


def load_genre_context(genre: str, descriptions_path: str = "data/genre_descriptions.txt") -> str:
    """Return the genre description paragraph for the given genre, or empty string."""
    if genre in _GENRE_CACHE:
        return _GENRE_CACHE[genre]

    try:
        with open(descriptions_path, encoding="utf-8") as f:
            content = f.read()

        blocks = [b.strip() for b in content.strip().split("\n\n") if b.strip()]
        for block in blocks:
            lines = block.splitlines()
            if lines and lines[0].strip().lower() == genre.lower():
                text = "\n".join(lines[1:]).strip()
                _GENRE_CACHE[genre] = text
                return text
    except FileNotFoundError:
        logger.warning("genre_descriptions.txt not found at %s", descriptions_path)
    except Exception as exc:
        logger.error("Error reading genre descriptions: %s", exc)

    _GENRE_CACHE[genre] = ""
    return ""


def _build_context(
    user_prefs: Dict,
    top_songs: List[Tuple[Dict, float, List[str]]],
    genre_context: str,
) -> str:
    lines = []

    lines.append("USER PREFERENCES:")
    lines.append(f"  Genre: {user_prefs.get('genre', '?')}  |  Mood: {user_prefs.get('mood', '?')}")
    lines.append(
        f"  Energy: {user_prefs.get('energy', '?')}  |  "
        f"Decade: {user_prefs.get('preferred_decade', '?')}  |  "
        f"Mood tag: {user_prefs.get('preferred_mood_tag', 'any')}"
    )

    if genre_context:
        lines.append(f"\nGENRE CONTEXT ({user_prefs.get('genre', '?')}):")
        lines.append(f"  {genre_context[:300]}")

    lines.append(f"\nTOP {len(top_songs)} RETRIEVED SONGS:")
    for i, (song, score, reasons) in enumerate(top_songs, 1):
        lines.append(
            f"  #{i}  {song['title']} by {song['artist']}"
            f"  |  Score: {score:.2f}/6.80"
            f"  |  Genre: {song['genre']}  Mood: {song['mood']}  Tag: {song.get('mood_tag', '')}"
            f"  |  Decade: {song.get('release_decade', '?')}  Pop: {song.get('popularity', '?')}"
        )
        lines.append(f"       Why matched: {'; '.join(reasons[:4])}")

    return "\n".join(lines)


SYSTEM_PROMPT = (
    "You are a friendly music recommendation assistant. "
    "You will receive a user's taste preferences, a genre description, "
    "and a list of songs that were retrieved and scored for them. "
    "Explain in 3-5 conversational sentences why these specific songs are a good match, "
    "referencing the scores, genres, moods, and decades provided. "
    "Be specific — mention song titles and artists by name. "
    "Do not make up songs or attributes that are not in the context."
)


def explain_with_claude(
    user_prefs: Dict,
    top_songs: List[Tuple[Dict, float, List[str]]],
    query: str = "Why are these songs a good match for my preferences?",
    descriptions_path: str = "data/genre_descriptions.txt",
) -> str:
    if not top_songs:
        logger.warning("explain_with_claude called with empty song list — skipping API call")
        return (
            f"{FALLBACK_PREFIX} No songs were retrieved. "
            "Try adjusting your genre or mood preferences."
        )

    songs_for_context = top_songs[:3]
    genre = user_prefs.get("genre", "")
    genre_context = load_genre_context(genre, descriptions_path)
    context_block = _build_context(user_prefs, songs_for_context, genre_context)

    logger.info(
        "RAG call: genre=%s mood=%s songs=%d",
        genre,
        user_prefs.get("mood", "?"),
        len(songs_for_context),
    )

    user_message = f"{context_block}\n\nUser question: {query}"

    try:
        client = _get_client()
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},
                }
            ],
            messages=[{"role": "user", "content": user_message}],
        )
        text = response.content[0].text.strip()

        if len(text) < 20:
            logger.warning("Claude response too short (%d chars) — using fallback", len(text))
            return _rule_based_fallback(top_songs)

        return text

    except anthropic.APIError as exc:
        logger.warning("Claude API error (%s: %s) — using fallback", type(exc).__name__, exc)
        return _rule_based_fallback(top_songs)
    except Exception as exc:
        logger.error("Unexpected error in explain_with_claude: %s", exc)
        return _rule_based_fallback(top_songs)


def _rule_based_fallback(top_songs: List[Tuple[Dict, float, List[str]]]) -> str:
    lines = [f"{FALLBACK_PREFIX} Here are your top matches based on your preferences:"]
    for i, (song, score, reasons) in enumerate(top_songs[:3], 1):
        lines.append(
            f"  #{i} {song['title']} by {song['artist']} "
            f"(score {score:.2f}/6.80): {'; '.join(reasons[:2])}"
        )
    return "\n".join(lines)
