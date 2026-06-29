"""Application configuration loaded from environment variables."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()

SAMPLE_RATE = 16_000
CHANNELS = 1
FRAME_SAMPLES = 512


@dataclass
class Settings:
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    elevenlabs_api_key: str = os.getenv("ELEVENLABS_API_KEY", "")
    elevenlabs_voice_id: str = os.getenv("ELEVENLABS_VOICE_ID", "")

    source_lang: str = os.getenv("SOURCE_LANG", "en")
    target_lang: str = os.getenv("TARGET_LANG", "es")
    tts_backend: str = os.getenv("TTS_BACKEND", "elevenlabs")

    stt_model: str = "whisper-large-v3-turbo"
    llm_model: str = "llama-3.1-8b-instant"

    def validate(self) -> None:
        if not self.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is required for speech-to-text and translation.")
        if self.tts_backend == "elevenlabs" and not self.elevenlabs_api_key:
            raise RuntimeError(
                "TTS_BACKEND=elevenlabs requires ELEVENLABS_API_KEY. "
                "Set it, or use TTS_BACKEND=xtts for the local CPU backend."
            )


settings = Settings()
