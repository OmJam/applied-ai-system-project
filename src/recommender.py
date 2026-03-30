import csv
from typing import List, Dict, Tuple
from dataclasses import asdict, dataclass

TEMPO_MIN = 60.0
TEMPO_MAX = 168.0

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

@dataclass
class UserProfile:
    """
    Represents a user's taste preferences.
    Required by tests/test_recommender.py
    """
    favorite_genre: str
    favorite_mood: str
    target_energy: float
    target_valence: float
    target_acousticness: float
    target_tempo: float
    target_danceability: float

class Recommender:
    """
    OOP implementation of the recommendation logic.
    Required by tests/test_recommender.py

    Scoring weights (out of 10):
        Energy          3.5  — raised: numeric proximity now the dominant signal
        Genre match     1.5  — halved: genre is a soft guide, not a hard gate
        Mood match      1.5  — contextual refinement
        Valence         1.5  — emotional tone, differentiates within mood
        Acousticness    1.0  — texture/timbre preference
        Tempo           0.5  — minor refinement, normalized to dataset range
        Danceability    0.5  — minor refinement
        ──────────────────
        Total          10.0
    """
    def __init__(self, songs: List[Song]):
        self.songs = songs

    def _score(self, user: UserProfile, song: Song) -> float:
        user_dict = {
            "genre": user.favorite_genre,   "mood": user.favorite_mood,
            "energy": user.target_energy,   "valence": user.target_valence,
            "acousticness": user.target_acousticness,
            "tempo_bpm": user.target_tempo, "danceability": user.target_danceability,
        }
        score, _ = score_song(user_dict, asdict(song))
        return score

    def recommend(self, user: UserProfile, k: int = 5) -> List[Song]:
        ranked = sorted(self.songs, key=lambda s: self._score(user, s), reverse=True)
        return ranked[:k]

    def explain_recommendation(self, user: UserProfile, song: Song) -> str:
        user_dict = {
            "genre": user.favorite_genre,   "mood": user.favorite_mood,
            "energy": user.target_energy,   "valence": user.target_valence,
            "acousticness": user.target_acousticness,
            "tempo_bpm": user.target_tempo, "danceability": user.target_danceability,
        }
        _, explanation = score_song(user_dict, asdict(song))
        return explanation

def load_songs(csv_path: str) -> List[Dict]:
    """
    Loads songs from a CSV file.
    Required by src/main.py
    """
    songs = []
    with open(csv_path, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            songs.append({
                "id":           int(row["id"]),
                "title":        row["title"],
                "artist":       row["artist"],
                "genre":        row["genre"],
                "mood":         row["mood"],
                "energy":       float(row["energy"]),
                "tempo_bpm":    float(row["tempo_bpm"]),
                "valence":      float(row["valence"]),
                "danceability": float(row["danceability"]),
                "acousticness": float(row["acousticness"]),
            })
    print(f"Loaded {len(songs)} songs from {csv_path}")
    return songs

def score_song(user_prefs: Dict, song: Dict) -> Tuple[float, str]:
    """
    Single source of truth for scoring logic. Judges one song against user_prefs.
    Returns (score, explanation). Called by Recommender._score,
    Recommender.explain_recommendation, and recommend_songs.
    Missing numeric keys default to 0.5 (neutral). Missing categorical keys
    default to "" (guaranteed no match).
    """
    genre_pts    = 1.5 if song["genre"] == user_prefs.get("genre", "") else 0.0
    mood_pts     = 1.5 if song["mood"]  == user_prefs.get("mood",  "") else 0.0
    energy_pts   = 3.5 * (1.0 - abs(song["energy"]       - user_prefs.get("energy",       0.5)))
    valence_pts  = 1.5 * (1.0 - abs(song["valence"]      - user_prefs.get("valence",      0.5)))
    acoustic_pts = 1.0 * (1.0 - abs(song["acousticness"] - user_prefs.get("acousticness", 0.5)))

    song_tempo_norm = (song["tempo_bpm"]                  - TEMPO_MIN) / (TEMPO_MAX - TEMPO_MIN)
    user_tempo_norm = (user_prefs.get("tempo_bpm", 114.0) - TEMPO_MIN) / (TEMPO_MAX - TEMPO_MIN)
    tempo_pts    = 0.5 * (1.0 - abs(song_tempo_norm - user_tempo_norm))

    dance_pts    = 0.5 * (1.0 - abs(song["danceability"] - user_prefs.get("danceability", 0.5)))

    total = genre_pts + mood_pts + energy_pts + valence_pts + acoustic_pts + tempo_pts + dance_pts

    genre_label = f"matched ({song['genre']})" if genre_pts > 0 else f"no match ({song['genre']} ≠ {user_prefs.get('genre', 'none')})"
    mood_label  = f"matched ({song['mood']})"  if mood_pts  > 0 else f"no match ({song['mood']} ≠ {user_prefs.get('mood',  'none')})"
    explanation = "\n".join([
        f'"{song["title"]}" scored {total:.2f}/10',
        f"  +{genre_pts:.1f} genre — {genre_label}",
        f"  +{mood_pts:.1f} mood — {mood_label}",
        f"  +{energy_pts:.2f} energy — song {song['energy']:.2f} vs target {user_prefs.get('energy', 0.5):.2f}",
        f"  +{valence_pts:.2f} valence — song {song['valence']:.2f} vs target {user_prefs.get('valence', 0.5):.2f}",
        f"  +{acoustic_pts:.2f} acousticness — song {song['acousticness']:.2f} vs target {user_prefs.get('acousticness', 0.5):.2f}",
        f"  +{tempo_pts:.2f} tempo — song {song['tempo_bpm']:.0f} BPM vs target {user_prefs.get('tempo_bpm', 114.0):.0f} BPM",
        f"  +{dance_pts:.2f} danceability — song {song['danceability']:.2f} vs target {user_prefs.get('danceability', 0.5):.2f}",
    ])
    return total, explanation


def recommend_songs(user_prefs: Dict, songs: List[Dict], k: int = 5) -> List[Tuple[Dict, float, str]]:
    """
    Scores every song with score_song, then returns the top k sorted highest to lowest.
    sorted() is used over .sort() because it returns a new list (catalog unchanged)
    and can be immediately sliced with [:k] in one expression.
    """
    scored = [(song, *score_song(user_prefs, song)) for song in songs]
    return sorted(scored, key=lambda x: x[1], reverse=True)[:k]
