"""Command-line entry point for Polyglot Voice Stream.

Usage:
    python main.py
    python main.py --clone NAME sample1.wav [sample2.wav ...]
"""
import sys

from src.pipeline import Pipeline


def clone(args: list[str]) -> None:
    from src.tts import ElevenLabsTTS

    if not args or len(args) < 2:
        print("Usage: python main.py --clone NAME sample1.wav [sample2.wav ...]")
        return
    name, samples = args[0], args[1:]
    voice_id = ElevenLabsTTS().clone_voice(name, samples)
    print(f"Cloned '{name}'. Set ELEVENLABS_VOICE_ID={voice_id} in your .env file.")


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--clone":
        clone(sys.argv[2:])
        return
    Pipeline().run()


if __name__ == "__main__":
    main()
