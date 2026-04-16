"""
Unit tests for the agent's tool functions and guardrails.

These tests verify the deterministic parts of the agentic workflow —
the tools that the LLM calls — without requiring an API key.
"""

from src.agent import get_recommendations, get_catalog, VALID_GENRES, VALID_MOODS


# ── get_recommendations: basic behavior ──────────────────────────────────────

class TestGetRecommendations:

    def test_returns_k_results(self):
        result = get_recommendations(genre="lofi", mood="chill", energy=0.35, k=3)
        assert len(result["recommendations"]) == 3

    def test_results_sorted_by_score_descending(self):
        result = get_recommendations(energy=0.8, valence=0.7)
        scores = [r["score"] for r in result["recommendations"]]
        assert scores == sorted(scores, reverse=True)

    def test_lofi_profile_returns_lofi_first(self):
        result = get_recommendations(
            genre="lofi", mood="chill", energy=0.35,
            valence=0.58, acousticness=0.80, tempo_bpm=76.0,
        )
        top = result["recommendations"][0]
        assert top["genre"] == "lofi"

    def test_rock_profile_returns_rock_first(self):
        result = get_recommendations(
            genre="rock", mood="intense", energy=0.92,
            valence=0.40, acousticness=0.08, tempo_bpm=148.0,
        )
        top = result["recommendations"][0]
        assert top["genre"] == "rock"

    def test_high_energy_party_returns_high_energy_top(self):
        result = get_recommendations(
            mood="hype", energy=0.95, danceability=0.90, valence=0.85,
        )
        top = result["recommendations"][0]
        assert top["energy"] >= 0.80

    def test_ghost_genre_still_returns_results(self):
        """A genre not in the catalog should still produce recommendations
        by falling back on numeric proximity."""
        result = get_recommendations(genre="k-pop", mood="happy", energy=0.80)
        assert len(result["recommendations"]) == 5
        assert result["recommendations"][0]["score"] > 0

    def test_profile_used_is_returned(self):
        result = get_recommendations(genre="jazz", mood="relaxed", energy=0.40)
        assert result["profile_used"]["genre"] == "jazz"
        assert result["profile_used"]["mood"] == "relaxed"
        assert result["profile_used"]["energy"] == 0.40


# ── get_recommendations: guardrails ──────────────────────────────────────────

class TestGuardrails:

    def test_energy_clamped_above_one(self):
        result = get_recommendations(energy=5.0)
        assert result["profile_used"]["energy"] == 1.0

    def test_energy_clamped_below_zero(self):
        result = get_recommendations(energy=-2.0)
        assert result["profile_used"]["energy"] == 0.0

    def test_tempo_clamped_to_range(self):
        result = get_recommendations(tempo_bpm=999.0)
        assert result["profile_used"]["tempo_bpm"] == 168.0

    def test_tempo_clamped_below_min(self):
        result = get_recommendations(tempo_bpm=10.0)
        assert result["profile_used"]["tempo_bpm"] == 60.0

    def test_k_clamped_to_catalog_size(self):
        result = get_recommendations(k=100)
        assert len(result["recommendations"]) == 18

    def test_k_minimum_is_one(self):
        result = get_recommendations(k=0)
        assert len(result["recommendations"]) == 1

    def test_defaults_produce_valid_output(self):
        """Calling with no arguments should not crash."""
        result = get_recommendations()
        assert len(result["recommendations"]) == 5
        assert result["confidence"] >= 0.0


# ── get_recommendations: confidence scoring ──────────────────────────────────

class TestConfidenceScoring:

    def test_strong_match_has_high_confidence(self):
        """A perfect lofi/chill profile should produce high confidence."""
        result = get_recommendations(
            genre="lofi", mood="chill", energy=0.35,
            valence=0.58, acousticness=0.80, tempo_bpm=76.0,
        )
        assert result["confidence"] >= 0.55

    def test_neutral_profile_has_lower_confidence(self):
        """All-midpoint profile with no genre/mood should produce lower confidence
        because everything scores similarly."""
        result = get_recommendations(
            genre="", mood="", energy=0.5, valence=0.5,
            acousticness=0.5, tempo_bpm=114.0, danceability=0.5,
        )
        strong = get_recommendations(
            genre="lofi", mood="chill", energy=0.35,
            valence=0.58, acousticness=0.80, tempo_bpm=76.0,
        )
        assert result["confidence"] < strong["confidence"]

    def test_confidence_between_zero_and_one(self):
        result = get_recommendations(energy=0.5)
        assert 0.0 <= result["confidence"] <= 1.0

    def test_match_quality_reflects_top_score(self):
        result = get_recommendations(
            genre="lofi", mood="chill", energy=0.35, acousticness=0.80,
        )
        top_score = result["recommendations"][0]["score"]
        assert result["match_quality"] == round(top_score / 10.0, 2)


# ── get_catalog ──────────────────────────────────────────────────────────────

class TestGetCatalog:

    def test_unfiltered_returns_all_songs(self):
        result = get_catalog()
        assert result["total_songs"] == 18

    def test_filter_by_genre(self):
        result = get_catalog(genre="lofi")
        assert result["total_songs"] == 3
        assert all(s["genre"] == "lofi" for s in result["songs"])

    def test_filter_by_mood(self):
        result = get_catalog(mood="chill")
        assert result["total_songs"] >= 1
        assert all(s["mood"] == "chill" for s in result["songs"])

    def test_filter_nonexistent_genre_returns_empty(self):
        result = get_catalog(genre="k-pop")
        assert result["total_songs"] == 0
        assert result["songs"] == []

    def test_available_genres_listed(self):
        result = get_catalog()
        assert set(VALID_GENRES) == set(result["available_genres"])

    def test_available_moods_listed(self):
        result = get_catalog()
        assert set(VALID_MOODS) == set(result["available_moods"])

    def test_case_insensitive_filtering(self):
        result = get_catalog(genre="Lofi")
        assert result["total_songs"] == 3
