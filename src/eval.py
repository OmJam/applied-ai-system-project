"""
Evaluation harness for the music recommender agent.

Tests predefined queries against expected outcomes to measure system
reliability. Does NOT require an API key — it tests the tool layer
directly (simulating what the LLM would call).

Run:  python -m src.eval
"""

from .agent import get_recommendations


# ── Test cases ───────────────────────────────────────────────────────────────
# Each case simulates an LLM-translated query with expected properties
# of the top result. This tests: did the scorer + guardrails produce
# a sensible ranking for this type of request?

EVAL_CASES = [
    {
        "name": "Chill lofi study music",
        "params": {
            "genre": "lofi", "mood": "chill", "energy": 0.35,
            "valence": 0.58, "acousticness": 0.80, "tempo_bpm": 76.0,
        },
        "expect": lambda top, res: top["genre"] == "lofi",
        "why": "Top result should be lofi when genre and features align",
    },
    {
        "name": "High-energy party music",
        "params": {
            "mood": "hype", "energy": 0.95, "danceability": 0.92,
            "valence": 0.85, "tempo_bpm": 135.0,
        },
        "expect": lambda top, res: top["energy"] >= 0.80 and top["score"] >= 7.0,
        "why": "Top result should be high-energy with a strong score",
    },
    {
        "name": "Sad emotional songs",
        "params": {
            "mood": "sad", "energy": 0.40, "valence": 0.25,
            "acousticness": 0.70, "tempo_bpm": 72.0,
        },
        "expect": lambda top, res: top["valence"] <= 0.55,
        "why": "Top result should lean toward low valence (darker tone)",
    },
    {
        "name": "Intense workout rock",
        "params": {
            "genre": "rock", "mood": "intense", "energy": 0.92,
            "valence": 0.40, "acousticness": 0.08, "tempo_bpm": 148.0,
        },
        "expect": lambda top, res: top["genre"] == "rock",
        "why": "Top result should be rock when genre + features match",
    },
    {
        "name": "Ghost genre (k-pop) graceful fallback",
        "params": {
            "genre": "k-pop", "mood": "happy", "energy": 0.80,
            "valence": 0.85, "danceability": 0.90, "tempo_bpm": 120.0,
        },
        "expect": lambda top, res: (
            top["score"] > 0 and res["confidence"] > 0
        ),
        "why": "System should still return results via numeric fallback",
    },
    {
        "name": "Contradictory: acoustic + high energy",
        "params": {
            "energy": 0.90, "acousticness": 0.90, "valence": 0.35,
            "tempo_bpm": 140.0,
        },
        "expect": lambda top, res: top["energy"] >= 0.60 or top["acousticness"] >= 0.60,
        "why": "System should compromise toward at least one requested feature",
    },
    {
        "name": "Confidence drops for neutral profile",
        "params": {
            "genre": "", "mood": "", "energy": 0.5, "valence": 0.5,
            "acousticness": 0.5, "tempo_bpm": 114.0, "danceability": 0.5,
        },
        "expect": lambda top, res: res["confidence"] < 0.65,
        "why": "No strong preferences should produce low confidence",
    },
    {
        "name": "All results returned when k=18",
        "params": {"energy": 0.5, "k": 18},
        "expect": lambda top, res: len(res["recommendations"]) == 18,
        "why": "Should return entire catalog when k equals catalog size",
    },
]


# ── Runner ───────────────────────────────────────────────────────────────────

def run_eval() -> None:
    passed = 0
    failed = 0
    total_confidence = 0.0
    results_detail = []

    print()
    print("=" * 60)
    print("  VibeMatch Evaluation Harness")
    print("=" * 60)
    print()

    for case in EVAL_CASES:
        result = get_recommendations(**case["params"])
        top = result["recommendations"][0]
        confidence = result["confidence"]
        total_confidence += confidence

        try:
            ok = case["expect"](top, result)
        except Exception as e:
            ok = False
            case["why"] += f" (check raised: {e})"

        status = "PASS" if ok else "FAIL"
        if ok:
            passed += 1
        else:
            failed += 1

        marker = "+" if ok else "X"
        results_detail.append((marker, case["name"], top["title"], top["score"], confidence))

        print(f"  [{marker}] {case['name']}")
        print(f"      Top: {top['title']} by {top['artist']} [{top['score']}/10]")
        print(f"      Confidence: {confidence}")
        if not ok:
            print(f"      EXPECTED: {case['why']}")
        print()

    avg_confidence = total_confidence / len(EVAL_CASES) if EVAL_CASES else 0

    print("-" * 60)
    print(f"  Results: {passed}/{passed + failed} passed")
    print(f"  Avg confidence: {avg_confidence:.2f}")
    print("-" * 60)
    print()

    # One-line summary for the README
    print("Summary for README:")
    print(
        f"  {passed} out of {passed + failed} eval cases passed. "
        f"Confidence scores averaged {avg_confidence:.2f}."
    )
    if failed:
        failed_names = [d[1] for d in results_detail if d[0] == "X"]
        print(f"  Struggled with: {', '.join(failed_names)}")
    print()


if __name__ == "__main__":
    run_eval()
