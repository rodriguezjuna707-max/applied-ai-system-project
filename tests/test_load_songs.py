import pytest
from src.recommender import load_songs


def test_load_songs_returns_correct_count():
    songs = load_songs("data/songs.csv")
    assert len(songs) == 18


def test_load_songs_numeric_fields_are_floats():
    songs = load_songs("data/songs.csv")
    s = songs[0]
    assert isinstance(s["energy"], float)
    assert isinstance(s["popularity"], float)
    assert isinstance(s["instrumentalness"], float)
    assert isinstance(s["liveness"], float)


def test_load_songs_string_fields_present():
    songs = load_songs("data/songs.csv")
    s = songs[0]
    assert isinstance(s["genre"], str)
    assert isinstance(s["mood"], str)
    assert isinstance(s["release_decade"], str)
    assert isinstance(s["mood_tag"], str)


def test_load_songs_file_not_found_raises():
    with pytest.raises(FileNotFoundError):
        load_songs("data/does_not_exist.csv")
