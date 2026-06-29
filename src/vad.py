"""Voice activity detection that segments a frame stream into utterances."""
import numpy as np
import torch
from silero_vad import load_silero_vad

from .config import FRAME_SAMPLES, SAMPLE_RATE


class UtteranceDetector:
    """Accumulates speech frames and emits a complete utterance on silence."""

    def __init__(self, speech_threshold: float = 0.5, silence_ms: int = 600) -> None:
        self.model = load_silero_vad()
        self.threshold = speech_threshold
        frame_ms = 1000 * FRAME_SAMPLES / SAMPLE_RATE
        self.silence_limit = max(1, int(silence_ms / frame_ms))

        self._buffer: list[np.ndarray] = []
        self._silence_run = 0
        self._triggered = False

    def push(self, frame: np.ndarray) -> np.ndarray | None:
        """Add one frame and return a finished utterance, or None if still listening."""
        prob = self.model(torch.from_numpy(frame), SAMPLE_RATE).item()
        is_speech = prob >= self.threshold

        if is_speech:
            self._triggered = True
            self._silence_run = 0
            self._buffer.append(frame)
        elif self._triggered:
            self._buffer.append(frame)
            self._silence_run += 1
            if self._silence_run >= self.silence_limit:
                return self._flush()
        return None

    def _flush(self) -> np.ndarray:
        utterance = (
            np.concatenate(self._buffer) if self._buffer else np.array([], dtype=np.float32)
        )
        self._buffer.clear()
        self._silence_run = 0
        self._triggered = False
        return utterance
