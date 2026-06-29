"""Microphone capture and audio playback."""
import queue

import numpy as np
import sounddevice as sd

from .config import CHANNELS, FRAME_SAMPLES, SAMPLE_RATE


class MicStream:
    """Streams fixed-size mono frames from the default input device."""

    def __init__(self) -> None:
        self.frames: "queue.Queue[np.ndarray]" = queue.Queue()
        self._stream: sd.InputStream | None = None

    def _callback(self, indata, _frames, _time, status) -> None:
        if status:
            print(f"[audio] {status}")
        self.frames.put(indata.copy().reshape(-1))

    def __enter__(self) -> "MicStream":
        self._stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            blocksize=FRAME_SAMPLES,
            dtype="float32",
            callback=self._callback,
        )
        self._stream.start()
        return self

    def __exit__(self, *_exc) -> None:
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()


def play(pcm_float: np.ndarray, sample_rate: int = SAMPLE_RATE) -> None:
    """Play a float32 waveform, blocking until playback completes."""
    sd.play(pcm_float, samplerate=sample_rate)
    sd.wait()
