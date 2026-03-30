"""
Command line runner for the Music Recommender Simulation.

This file helps you quickly run and test your recommender.

You will implement the functions in recommender.py:
- load_songs
- score_song
- recommend_songs
"""

from .recommender import load_songs, recommend_songs


# ── Standard profiles ──────────────────────────────────────────────────────────

HIGH_ENERGY_POP = {
    "genre": "pop", "mood": "happy",
    "energy": 0.90, "valence": 0.85,
    "acousticness": 0.10, "tempo_bpm": 128.0, "danceability": 0.88,
}

CHILL_LOFI = {
    "genre": "lofi", "mood": "chill",
    "energy": 0.38, "valence": 0.58,
    "acousticness": 0.80, "tempo_bpm": 76.0, "danceability": 0.58,
}

DEEP_INTENSE_ROCK = {
    "genre": "rock", "mood": "intense",
    "energy": 0.92, "valence": 0.40,
    "acousticness": 0.08, "tempo_bpm": 148.0, "danceability": 0.62,
}

# ── Adversarial / edge-case profiles ───────────────────────────────────────────

# Contradiction: high energy (0.95) but sad mood — will the system pick angry
# metal (energy match, mood miss) or slow soul (mood adjacent, energy miss)?
CONFLICTED_SAD_BANGER = {
    "genre": "soul", "mood": "sad",
    "energy": 0.95, "valence": 0.25,
    "acousticness": 0.50, "tempo_bpm": 140.0, "danceability": 0.70,
}

# Ghost genre: requests a genre that doesn't exist in the catalog.
# No song earns the 3.0 genre bonus — ranking falls entirely on numeric features.
# Reveals which song is the "most average" match when genre filtering fails.
NONEXISTENT_GENRE = {
    "genre": "k-pop", "mood": "happy",
    "energy": 0.80, "valence": 0.85,
    "acousticness": 0.10, "tempo_bpm": 120.0, "danceability": 0.90,
}

# All midpoints: every numeric target is 0.5, no categorical preference set.
# Every song scores the same on genre and mood (all miss), so numeric spread
# decides the ranking — surfaces the "most average" songs in the catalog.
ALL_MIDPOINT = {
    "genre": "", "mood": "",
    "energy": 0.5, "valence": 0.5,
    "acousticness": 0.5, "tempo_bpm": 114.0, "danceability": 0.5,
}

# Paradox: wants very high acousticness (folk/classical texture) but intense mood.
# No single song satisfies both — the system must pick a compromise.
ACOUSTIC_BUT_INTENSE = {
    "genre": "folk", "mood": "intense",
    "energy": 0.88, "valence": 0.35,
    "acousticness": 0.90, "tempo_bpm": 140.0, "danceability": 0.50,
}


PROFILES = [
    ("High-Energy Pop",       HIGH_ENERGY_POP),
    ("Chill Lofi",            CHILL_LOFI),
    ("Deep Intense Rock",     DEEP_INTENSE_ROCK),
    ("Conflicted: Sad Banger",CONFLICTED_SAD_BANGER),
    ("Ghost Genre (k-pop)",   NONEXISTENT_GENRE),
    ("All Midpoint",          ALL_MIDPOINT),
    ("Acoustic but Intense",  ACOUSTIC_BUT_INTENSE),
]


def main() -> None:
    songs = load_songs("data/songs.csv")
    print()

    for label, user_prefs in PROFILES:
        print("=" * 60)
        print(f"  PROFILE: {label}")
        print("=" * 60)

        recommendations = recommend_songs(user_prefs, songs, k=5)
        for rank, (song, score, explanation) in enumerate(recommendations, start=1):
            print(f"\n  #{rank}  {song['title']} by {song['artist']}  [{score:.2f}/10]")
            for line in explanation.split("\n")[1:]:   # skip the header line, already shown
                print(f"      {line.strip()}")
        print()


if __name__ == "__main__":
    main()
