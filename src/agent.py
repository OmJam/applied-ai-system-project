"""
Agentic music recommender powered by Google Gemini.

The agent translates natural language into tool calls against the
deterministic scorer and responds conversationally.

Architecture:
    User (natural language) -> Gemini Agent -> Tools -> score_song() -> Agent -> User
"""

import os
import json
import logging

from google import genai
from google.genai import types
from dotenv import load_dotenv

from .recommender import load_songs, recommend_songs

load_dotenv()

# ── Logging ──────────────────────────────────────────────────────────────────

def _setup_logger() -> logging.Logger:
    log = logging.getLogger("vibematch")
    if log.handlers:
        return log
    log.setLevel(logging.INFO)
    fmt = logging.Formatter("%(asctime)s %(message)s", datefmt="%H:%M:%S")

    console = logging.StreamHandler()
    console.setFormatter(fmt)
    log.addHandler(console)

    os.makedirs("logs", exist_ok=True)
    fh = logging.FileHandler("logs/agent.log")
    fh.setFormatter(fmt)
    log.addHandler(fh)

    return log

logger = _setup_logger()

# ── Song catalog (loaded once) ───────────────────────────────────────────────

SONGS = load_songs("data/songs.csv")
VALID_GENRES = sorted(set(s["genre"] for s in SONGS))
VALID_MOODS = sorted(set(s["mood"] for s in SONGS))

# ── Tool functions ───────────────────────────────────────────────────────────

def get_recommendations(
    genre: str = "",
    mood: str = "",
    energy: float = 0.5,
    valence: float = 0.5,
    acousticness: float = 0.5,
    tempo_bpm: float = 114.0,
    danceability: float = 0.5,
    k: int = 5,
) -> dict:
    """Get song recommendations based on user preferences using the
    deterministic scoring engine.

    Args:
        genre: Preferred genre. Options: pop, lofi, rock, ambient, jazz,
            synthwave, indie pop, hip-hop, classical, r&b, metal, folk,
            edm, soul, latin. Empty string for no preference.
        mood: Preferred mood. Options: happy, chill, intense, relaxed,
            focused, moody, romantic, melancholic, hype, angry, nostalgic,
            euphoric, sad, uplifting. Empty string for no preference.
        energy: Energy level 0.0 (calm) to 1.0 (intense). Default 0.5.
        valence: Positiveness 0.0 (dark/sad) to 1.0 (happy). Default 0.5.
        acousticness: 0.0 (electronic) to 1.0 (acoustic). Default 0.5.
        tempo_bpm: Tempo in BPM, 60 (slow) to 168 (fast). Default 114.
        danceability: 0.0 (freeform) to 1.0 (strong beat). Default 0.5.
        k: Number of recommendations, 1-18. Default 5.

    Returns:
        Dict with recommendations list and the profile used.
    """
    # Guardrails: clamp to valid ranges
    energy = max(0.0, min(1.0, float(energy)))
    valence = max(0.0, min(1.0, float(valence)))
    acousticness = max(0.0, min(1.0, float(acousticness)))
    tempo_bpm = max(60.0, min(168.0, float(tempo_bpm)))
    danceability = max(0.0, min(1.0, float(danceability)))
    k = max(1, min(18, int(k)))

    user_prefs = {
        "genre": str(genre),
        "mood": str(mood),
        "energy": energy,
        "valence": valence,
        "acousticness": acousticness,
        "tempo_bpm": tempo_bpm,
        "danceability": danceability,
    }

    logger.info(
        f"[TOOL] get_recommendations -> genre={genre}, mood={mood}, "
        f"energy={energy:.2f}, valence={valence:.2f}, "
        f"acousticness={acousticness:.2f}, tempo={tempo_bpm:.0f}, "
        f"danceability={danceability:.2f}, k={k}"
    )

    results = recommend_songs(user_prefs, SONGS, k=k)

    recs = []
    for song, score, explanation in results:
        recs.append({
            "title": song["title"],
            "artist": song["artist"],
            "genre": song["genre"],
            "mood": song["mood"],
            "energy": song["energy"],
            "valence": song["valence"],
            "tempo_bpm": song["tempo_bpm"],
            "score": round(score, 2),
            "explanation": explanation,
        })

    # Confidence scoring: how well does the best match actually fit?
    # - match_quality: top score / 10 (0-1). High = strong match exists.
    # - separation: gap between #1 and #2. High = clear winner, low = toss-up.
    if recs:
        top = recs[0]["score"]
        second = recs[1]["score"] if len(recs) > 1 else 0.0
        match_quality = round(top / 10.0, 2)
        separation = round((top - second) / 10.0, 2)
        confidence = round(match_quality * 0.7 + min(separation * 2, 1.0) * 0.3, 2)

        logger.info(
            f"[RESULT] Top: {recs[0]['title']} by {recs[0]['artist']} "
            f"[{top}/10] confidence={confidence}"
        )
    else:
        match_quality = 0.0
        separation = 0.0
        confidence = 0.0

    return {
        "profile_used": user_prefs,
        "recommendations": recs,
        "confidence": confidence,
        "match_quality": match_quality,
        "separation": separation,
    }


def get_catalog(genre: str = "", mood: str = "") -> dict:
    """Browse the song catalog, optionally filtered by genre and/or mood.
    Use this to check what genres or moods are available.

    Args:
        genre: Filter by genre. Empty string for all.
        mood: Filter by mood. Empty string for all.

    Returns:
        Dict with matching songs and available genres/moods.
    """
    filtered = SONGS
    if genre:
        filtered = [s for s in filtered if s["genre"].lower() == genre.lower()]
    if mood:
        filtered = [s for s in filtered if s["mood"].lower() == mood.lower()]

    logger.info(
        f"[TOOL] get_catalog -> genre='{genre}', mood='{mood}' "
        f"-> {len(filtered)} songs"
    )

    return {
        "total_songs": len(filtered),
        "available_genres": VALID_GENRES,
        "available_moods": VALID_MOODS,
        "songs": [
            {
                "title": s["title"],
                "artist": s["artist"],
                "genre": s["genre"],
                "mood": s["mood"],
                "energy": s["energy"],
                "valence": s["valence"],
                "tempo_bpm": s["tempo_bpm"],
                "danceability": s["danceability"],
                "acousticness": s["acousticness"],
            }
            for s in filtered
        ],
    }


# ── Tool dispatch table ──────────────────────────────────────────────────────

TOOL_DISPATCH = {
    "get_recommendations": get_recommendations,
    "get_catalog": get_catalog,
}

# ── System prompt ────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """\
You are VibeMatch, a music recommendation agent. Users describe what kind of \
music they want in natural language, and you find the best matches from a \
catalog of 18 songs.

Your workflow:
1. Interpret the user's request and call get_recommendations with numeric \
parameters that match their intent. Translate their language to features:
   - "chill", "relaxing", "calm", "study" -> low energy (0.2-0.4), \
high acousticness (0.7-0.9), mood "chill" or "relaxed"
   - "energetic", "workout", "pump up", "party" -> high energy (0.8-1.0), \
high danceability (0.7-0.9), mood "hype" or "intense"
   - "sad", "emotional", "melancholy" -> low valence (0.2-0.4), \
mood "sad" or "melancholic"
   - "happy", "upbeat", "bright" -> high valence (0.7-0.9), \
mood "happy" or "uplifting"
   - "fast", "intense" -> high tempo (130-168 BPM), high energy
   - "slow", "gentle" -> low tempo (60-80 BPM), low energy
   - If no specific genre fits, leave genre as empty string.

2. Review the results. If the top picks don't match the user's intent well, \
adjust parameters and call get_recommendations again.

3. Present results conversationally. Include the song name, artist, score, \
and a brief reason why it matches. Keep it concise.

4. If the user wants to refine ("more upbeat", "something different"), \
adjust parameters and call get_recommendations again.

Rules:
- ALWAYS call get_recommendations to get results. Never invent songs or scores.
- Use get_catalog if you need to check what genres or moods are available.
- Be honest when the catalog lacks a great match. Explain the trade-off.
- Keep responses concise.
"""

# ── Guardrail: max tool-call rounds to prevent infinite loops ────────────────

MAX_TOOL_ROUNDS = 5

# ── Agent class ──────────────────────────────────────────────────────────────


class MusicAgent:
    """Agentic music recommender powered by Google Gemini.

    Interprets natural language, calls the deterministic scorer via tools,
    evaluates results, and responds conversationally.
    """

    MODEL = "gemini-2.0-flash"

    def __init__(self):
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError(
                "GOOGLE_API_KEY not found. "
                "Create a .env file in the project root with:\n"
                "  GOOGLE_API_KEY=your-key-here"
            )

        self.client = genai.Client(api_key=api_key)
        self.config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            tools=[get_recommendations, get_catalog],
        )
        self.chat = self.client.chats.create(
            model=self.MODEL, config=self.config,
        )
        logger.info("[INIT] MusicAgent ready (%s)", self.MODEL)

    def send(self, user_message: str) -> str:
        """Send a user message and return the agent's conversational response.

        Handles the full agentic loop: the model may call tools multiple
        times before producing a final text answer.
        """
        logger.info("[USER] %s", user_message)

        try:
            response = self.chat.send_message(message=user_message)

            # Agentic loop — resolve tool calls until the model responds with text
            rounds = 0
            while response.function_calls and rounds < MAX_TOOL_ROUNDS:
                rounds += 1
                tool_parts = []

                for fn_call in response.function_calls:
                    fn_name = fn_call.name
                    fn_args = dict(fn_call.args) if fn_call.args else {}

                    logger.info("[CALL] %s(%s)", fn_name, json.dumps(fn_args, default=str))

                    if fn_name in TOOL_DISPATCH:
                        try:
                            result = TOOL_DISPATCH[fn_name](**fn_args)
                        except TypeError as e:
                            logger.error("[ERROR] Bad args for %s: %s", fn_name, e)
                            result = {"error": str(e)}
                    else:
                        logger.warning("[WARN] Unknown tool: %s", fn_name)
                        result = {"error": f"Unknown tool: {fn_name}"}

                    tool_parts.append(
                        types.Part.from_function_response(
                            name=fn_name,
                            response={"result": result},
                        )
                    )

                response = self.chat.send_message(message=tool_parts)

            if rounds >= MAX_TOOL_ROUNDS:
                logger.warning("[WARN] Hit max tool rounds (%d)", MAX_TOOL_ROUNDS)

            reply = response.text
            logger.info("[AGENT] %s...", reply[:120])
            return reply

        except Exception as e:
            logger.error("[ERROR] %s", e)
            return f"Something went wrong: {e}"

    def reset(self):
        """Start a fresh conversation (clears chat history)."""
        self.chat = self.client.chats.create(
            model=self.MODEL, config=self.config,
        )
        logger.info("[RESET] Conversation cleared")
