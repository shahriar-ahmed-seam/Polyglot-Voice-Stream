# Polyglot Voice Stream

Real-time speech translation that preserves your own voice. You speak in one language and, within a couple of seconds, hear the translation spoken back in a clone of your voice.

The pipeline runs without a local GPU. The compute-heavy stages (speech recognition, translation, voice synthesis) are offloaded to inference APIs, while the latency-critical orchestration (capture, voice-activity detection, streaming) runs on CPU.

## Architecture

```
                    shared pipeline (src/)
  microphone ─► VAD ─► speech-to-text ─► translation ─► text-to-speech ─► playback
              (Silero)   (Groq Whisper)    (Groq LLM)   (ElevenLabs / XTTS)

  CLI  (main.py)    drives the pipeline directly on the local machine.
  Web  (server.py)  exposes it over a WebSocket; a Next.js client streams audio in and out.
```

| Stage | Component | Runs on |
| --- | --- | --- |
| Audio capture | `sounddevice` (CLI) / Web Audio API (browser) | CPU |
| Voice activity detection | Silero VAD | CPU |
| Speech-to-text | Groq `whisper-large-v3-turbo` | Cloud |
| Translation | Groq `llama-3.1-8b-instant` | Cloud |
| Text-to-speech | ElevenLabs, or Coqui XTTS-v2 (local CPU) | Cloud / CPU |

Stages are pipelined across threads (CLI) and an async event loop (server): one utterance is transcribed and translated while the previous one is still playing. End-to-end latency is typically 1.5–2.5s for short sentences.

## Project layout

```
.
├── main.py              Command-line interface
├── server.py            FastAPI WebSocket server (web backend)
├── Dockerfile           CPU-only backend image for Render / Railway / Fly.io
├── render.yaml          Render blueprint for one-click backend deploy
├── requirements.txt
├── src/                 Pipeline shared by the CLI and the server
│   ├── config.py        Environment-based settings
│   ├── audio_capture.py Microphone capture and playback
│   ├── vad.py           Utterance segmentation
│   ├── stt.py           Speech-to-text
│   ├── translate.py     Translation
│   ├── tts.py           Text-to-speech backends
│   └── pipeline.py      CLI orchestrator
└── web/                 Next.js frontend (deploy to Vercel, root directory = web)
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (web frontend only)
- A [Groq API key](https://console.groq.com) for speech-to-text and translation (free tier)
- An [ElevenLabs API key](https://elevenlabs.io) for cloud text-to-speech (free tier works; see the note on voice cloning below)

## Local development

Install the CPU builds of PyTorch and torchaudio first so the resolver does not pull CUDA packages (`torchaudio` is a Silero VAD dependency):

```bash
pip install torch==2.3.1 torchaudio==2.3.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Configure environment variables:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| --- | --- | --- |
| `GROQ_API_KEY` | Groq key for STT and translation | required |
| `ELEVENLABS_API_KEY` | ElevenLabs key | required for the `elevenlabs` backend |
| `ELEVENLABS_VOICE_ID` | Voice used for synthesis (cloned or stock) | required for the `elevenlabs` backend |
| `SOURCE_LANG` | Spoken language | `en` |
| `TARGET_LANG` | Target language | `es` |
| `TTS_BACKEND` | `elevenlabs` or `xtts` | `elevenlabs` |

### CLI

Optionally clone your voice once from a short, clean sample (~30s):

```bash
python main.py --clone "my-voice" voice_samples/me.wav
```

Set the printed id as `ELEVENLABS_VOICE_ID`, then run:

```bash
python main.py
```

Speak, pause, and hear the translation. `Ctrl+C` to stop.

### Web

```bash
# backend
uvicorn server:app --host 0.0.0.0 --port 8000

# frontend (second terminal)
cd web
npm install
cp .env.local.example .env.local        # NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
npm run dev
```

Open http://localhost:3000 and press **Start talking**.

## Deployment

The frontend and backend deploy to different platforms: Vercel's serverless functions cannot hold the long-lived WebSocket connection the audio stream requires, so the backend runs on a container host.

### Backend — Render (Railway / Fly.io also work)

The repository includes a `render.yaml` blueprint.

1. On Render, create a new **Blueprint** and connect this repository.
2. Provide the secret environment variables when prompted: `GROQ_API_KEY`, `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`.
3. Deploy. Verify the service at `https://<service>.onrender.com/health` (returns `{"ok": true, ...}`).

The `Dockerfile` builds a CPU-only image and binds to `$PORT`. Render terminates TLS, so the public endpoint is available over `wss://`.

### Frontend — Vercel

1. Import the repository in Vercel and set **Root Directory** to `web`. This is required — otherwise Vercel detects the Python files at the repository root and attempts to build the backend instead of the Next.js app.
2. Set the environment variable `NEXT_PUBLIC_WS_URL` to `wss://<service>.onrender.com/ws`.
3. Deploy.

A page served over HTTPS can only open a secure (`wss://`) WebSocket, so the backend must be reachable over TLS.

## Notes

**Voice cloning.** Cloning your own voice requires an ElevenLabs paid tier (Starter and above). On the free tier, set `ELEVENLABS_VOICE_ID` to a stock voice from the ElevenLabs dashboard; the full pipeline works, but the output uses a stock voice rather than a clone. The local `xtts` backend clones for free but needs several GB of RAM and does not fit on small free instances.

**Security.** API keys are read from environment variables and are never committed (`.env` is git-ignored). CORS is open (`*`) for convenience; restrict `allow_origins` in `server.py` to the deployed frontend origin before exposing the backend publicly.

**Cost and limits.** Groq's free tier is rate limited; ElevenLabs bills per synthesized character. Monitor usage for long sessions.

**Latency.** Lower `silence_ms` in `src/vad.py` (default 600) for faster turn-taking at the risk of clipping slow speakers. The `eleven_turbo_v2_5` model is used for low-latency synthesis.

## License

MIT
