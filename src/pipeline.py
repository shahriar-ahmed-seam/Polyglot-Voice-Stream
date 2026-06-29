"""Streaming translation pipeline for the command-line interface.

Stages run on separate threads connected by queues so that one utterance can be
transcribed and translated while the previous one is still playing back:

    microphone -> VAD -> [utterance queue] -> STT + translate + TTS -> [audio queue] -> playback
"""
import queue
import threading
import time

import numpy as np

from .audio_capture import MicStream, play
from .config import settings
from .stt import Transcriber
from .translate import Translator
from .tts import make_tts
from .vad import UtteranceDetector


class Pipeline:
    def __init__(self) -> None:
        settings.validate()
        self.vad = UtteranceDetector()
        self.stt = Transcriber()
        self.translator = Translator()
        self.tts = make_tts()

        self.utterances: "queue.Queue[np.ndarray]" = queue.Queue()
        self.audio_out: "queue.Queue[np.ndarray]" = queue.Queue()
        self._stop = threading.Event()

    def _process_worker(self) -> None:
        while not self._stop.is_set():
            try:
                utterance = self.utterances.get(timeout=0.2)
            except queue.Empty:
                continue
            started = time.time()
            text = self.stt.transcribe(utterance)
            if not text:
                continue
            translated = self.translator.translate(text)
            self.audio_out.put(self.tts.synthesize(translated))
            print(f"[{settings.source_lang}] {text}")
            print(f"[{settings.target_lang}] {translated}  ({time.time() - started:.2f}s)\n")

    def _playback_worker(self) -> None:
        while not self._stop.is_set():
            try:
                audio = self.audio_out.get(timeout=0.2)
            except queue.Empty:
                continue
            play(audio)

    def run(self) -> None:
        workers = [
            threading.Thread(target=self._process_worker, daemon=True),
            threading.Thread(target=self._playback_worker, daemon=True),
        ]
        for worker in workers:
            worker.start()

        print(f"Listening ({settings.source_lang} -> {settings.target_lang}). Press Ctrl+C to stop.\n")
        try:
            with MicStream() as mic:
                while True:
                    utterance = self.vad.push(mic.frames.get())
                    if utterance is not None and utterance.size > 0:
                        self.utterances.put(utterance)
        except KeyboardInterrupt:
            print("\nStopping...")
        finally:
            self._stop.set()
