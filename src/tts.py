"""Text-to-speech with voice cloning.

Backends:
    elevenlabs  Cloud voice cloning, near real-time. Requires an API key.
    xtts        Coqui XTTS-v2 running locally on CPU. Free and offline, but slower.
"""
from abc import ABC, abstractmethod

import numpy as np

from .config import SAMPLE_RATE, settings


class TTSBackend(ABC):
    @abstractmethod
    def synthesize(self, text: str) -> np.ndarray:
        """Return a float32 mono waveform sampled at SAMPLE_RATE."""


class ElevenLabsTTS(TTSBackend):
    def __init__(self) -> None:
        from elevenlabs.client import ElevenLabs

        self.client = ElevenLabs(api_key=settings.elevenlabs_api_key)
        self.voice_id = settings.elevenlabs_voice_id

    def clone_voice(self, name: str, sample_paths: list[str]) -> str:
        voice = self.client.clone(name=name, files=sample_paths)
        self.voice_id = voice.voice_id
        return voice.voice_id

    def synthesize(self, text: str) -> np.ndarray:
        if not self.voice_id:
            raise RuntimeError("ELEVENLABS_VOICE_ID is not set. Clone a voice first.")
        audio = self.client.text_to_speech.convert(
            voice_id=self.voice_id,
            model_id="eleven_turbo_v2_5",
            text=text,
            output_format=f"pcm_{SAMPLE_RATE}",
        )
        pcm_bytes = b"".join(audio)
        return np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32767.0


class XTTSLocal(TTSBackend):
    def __init__(self, speaker_wav: str = "voice_samples/me.wav") -> None:
        from TTS.api import TTS

        self.speaker_wav = speaker_wav
        self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2")

    def synthesize(self, text: str) -> np.ndarray:
        wav = self.model.tts(
            text=text,
            speaker_wav=self.speaker_wav,
            language=settings.target_lang,
        )
        return np.asarray(wav, dtype=np.float32)


def make_tts() -> TTSBackend:
    if settings.tts_backend == "xtts":
        return XTTSLocal()
    return ElevenLabsTTS()
