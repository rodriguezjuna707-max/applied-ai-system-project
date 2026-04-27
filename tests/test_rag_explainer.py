import pytest
from unittest.mock import patch, MagicMock
import anthropic

from src.rag_explainer import explain_with_claude, load_genre_context, FALLBACK_PREFIX, _GENRE_CACHE


SAMPLE_SONG = {
    "title": "Sunrise City",
    "artist": "Neon Echo",
    "genre": "pop",
    "mood": "happy",
    "mood_tag": "euphoric",
    "release_decade": "2020s",
    "popularity": 78.0,
    "energy": 0.82,
    "valence": 0.84,
    "danceability": 0.79,
    "acousticness": 0.18,
    "instrumentalness": 0.02,
    "liveness": 0.12,
}

SAMPLE_PREFS = {
    "genre": "pop",
    "mood": "happy",
    "energy": 0.9,
    "valence": 0.85,
    "danceability": 0.88,
    "acousticness": 0.05,
    "target_popularity": 85,
    "preferred_decade": "2020s",
    "preferred_mood_tag": "euphoric",
    "target_instrumentalness": 0.03,
    "target_liveness": 0.10,
}

SAMPLE_TOP_SONGS = [(SAMPLE_SONG, 5.84, ["genre match (pop) (+1.00)", "mood match (happy) (+1.00)"])]


def _make_mock_response(text: str):
    mock_resp = MagicMock()
    mock_resp.content = [MagicMock(text=text)]
    return mock_resp


def test_explain_with_claude_returns_string():
    with patch("src.rag_explainer._get_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(
            "Sunrise City is a great match because it perfectly fits your euphoric pop target."
        )
        mock_client_fn.return_value = mock_client

        result = explain_with_claude(SAMPLE_PREFS, SAMPLE_TOP_SONGS)

    assert isinstance(result, str)
    assert len(result) > 0
    assert not result.startswith(FALLBACK_PREFIX)


def test_explain_with_claude_empty_songs_skips_api():
    with patch("src.rag_explainer._get_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client

        result = explain_with_claude(SAMPLE_PREFS, [])

    mock_client.messages.create.assert_not_called()
    assert result.startswith(FALLBACK_PREFIX)


def test_explain_with_claude_fallback_on_api_error():
    with patch("src.rag_explender._get_client") if False else patch("src.rag_explainer._get_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.side_effect = anthropic.APIConnectionError(request=MagicMock())
        mock_client_fn.return_value = mock_client

        result = explain_with_claude(SAMPLE_PREFS, SAMPLE_TOP_SONGS)

    assert isinstance(result, str)
    assert len(result) > 0
    assert result.startswith(FALLBACK_PREFIX)


def test_explain_with_claude_short_response_uses_fallback():
    with patch("src.rag_explainer._get_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response("ok")
        mock_client_fn.return_value = mock_client

        result = explain_with_claude(SAMPLE_PREFS, SAMPLE_TOP_SONGS)

    assert result.startswith(FALLBACK_PREFIX)


def test_context_contains_song_title():
    with patch("src.rag_explainer._get_client") as mock_client_fn:
        mock_client = MagicMock()
        mock_client.messages.create.return_value = _make_mock_response(
            "Sunrise City matches your euphoric pop energy target perfectly."
        )
        mock_client_fn.return_value = mock_client

        explain_with_claude(SAMPLE_PREFS, SAMPLE_TOP_SONGS)

    call_args = mock_client.messages.create.call_args
    messages = call_args.kwargs.get("messages") or call_args[1].get("messages") or call_args[0][2]
    user_content = messages[0]["content"]
    assert "Sunrise City" in user_content


def test_load_genre_context_returns_text():
    _GENRE_CACHE.clear()
    text = load_genre_context("pop", "data/genre_descriptions.txt")
    assert isinstance(text, str)
    assert len(text) > 20


def test_load_genre_context_missing_file_returns_empty():
    _GENRE_CACHE.clear()
    text = load_genre_context("pop", "data/no_such_file.txt")
    assert text == ""


def test_load_genre_context_unknown_genre_returns_empty():
    _GENRE_CACHE.clear()
    text = load_genre_context("zydeco", "data/genre_descriptions.txt")
    assert text == ""
