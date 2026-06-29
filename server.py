"""WebSocket server that powers the browser frontend.

Protocol:
    Client -> server : binary frames of int16 PCM, mono, 16 kHz.
    Server -> client : per completed utterance,
        1. a text message: {"source": str, "target": str, "ms": int}
        2. a binary message of int16 PCM (16 kHz) to play back.

Run locally:
    uvicorn server:app --host 0.0.0.0 --port 8000
"""
import asyncio
import json
import time

import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from src.config import FRAME_SAMPLES, settings
from src.stt import Transcriber
from src.translate import Translator
from src.tts import make_tts
from src.vad import UtteranceDetector

settings.validate()

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

_stt = Transcriber()
_translator = Translator()
_tts = make_tts()


@app.get("/health")
def health() -> dict:
    return {"ok": True, "source": settings.source_lang, "target": settings.target_lang}


def _process(utterance: np.ndarray) -> tuple[str, str, np.ndarray]:
    text = _stt.transcribe(utterance)
    if not text:
        return "", "", np.array([], dtype=np.float32)
    translated = _translator.translate(text)
    return text, translated, _tts.synthesize(translated)


@app.websocket("/ws")
async def ws(socket: WebSocket) -> None:
    await socket.accept()
    vad = UtteranceDetector()
    pending = np.array([], dtype=np.float32)
    try:
        while True:
            chunk = await socket.receive_bytes()
            samples = np.frombuffer(chunk, dtype=np.int16).astype(np.float32) / 32767.0
            pending = np.concatenate([pending, samples])

            while pending.size >= FRAME_SAMPLES:
                frame, pending = pending[:FRAME_SAMPLES], pending[FRAME_SAMPLES:]
                utterance = vad.push(frame)
                if utterance is None or utterance.size == 0:
                    continue

                started = time.time()
                source, target, audio = await asyncio.to_thread(_process, utterance)
                if not source:
                    continue
                await socket.send_text(json.dumps(
                    {"source": source, "target": target, "ms": int((time.time() - started) * 1000)}
                ))
                pcm16 = np.clip(audio * 32767, -32768, 32767).astype(np.int16)
                await socket.send_bytes(pcm16.tobytes())
    except WebSocketDisconnect:
        pass
