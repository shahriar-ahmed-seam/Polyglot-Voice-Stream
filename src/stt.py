"""Speech-to-text using Groq-hosted Whisper."""
import io
import wave

import numpy as np
from groq import Groq

from .config import SAMPLE_RATE, settings


def _to_wav_bytes(pcm_float: np.ndarray) -> bytes:
    pcm_int16 = np.clip(pcm_float * 32767, -32768, 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SAMPLE_RATE)
        wf.writeframes(pcm_int16.tobytes())
    buf.seek(0)
    return buf.read()


class Transcriber:
    def __init__(self) -> None:
        self.client = Groq(api_key=settings.groq_api_key)

    def transcribe(self, pcm_float: np.ndarray) -> str:
        resp = self.client.audio.transcriptions.create(
            file=("utterance.wav", _to_wav_bytes(pcm_float)),
            model=settings.stt_model,
            language=settings.source_lang,
            response_format="text",
        )
        return str(resp).strip()
