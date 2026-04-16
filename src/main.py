"""
Music Recommender with Agentic Workflow.

Run:  python -m src.main
"""

from .agent import MusicAgent


def main() -> None:
    print()
    print("=" * 50)
    print("  VibeMatch - AI Music Recommender")
    print("=" * 50)
    print()
    print("Describe the music you're in the mood for.")
    print("Type 'quit' to exit or 'reset' to start over.")
    print()

    agent = MusicAgent()

    while True:
        try:
            user_input = input("You: ").strip()

            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "q"):
                print("\nGoodbye!")
                break
            if user_input.lower() == "reset":
                agent.reset()
                print("\n[Conversation reset]\n")
                continue

            response = agent.send(user_input)
            print(f"\nVibeMatch: {response}\n")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break


if __name__ == "__main__":
    main()
