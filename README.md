# Polyglot Voice Stream

Real-time speech translation that keeps your own voice. You speak in one language, and within a couple of seconds you hear the translation spoken back in a clone of your voice.

The entire pipeline runs without a local GPU. The GPU-bound work (speech recognition, translation, voice synthesis) is offloaded to fast inference APIs, while the latency-critical orchestration runs on CPU.

## How it works

```
                   ┌──────────────────────── shared pipeline (src/) ────────────────────────┐
  microphone ─►  VAD  ─►  speech-to-text  ─►  translation  ─►  text-to-speech  ─►  playback
                (Silero)     (Groq Whisper)     (Groq LLM)      (ElevenLabs / XTTS)
                   └────────────────────────────────────────────────────────────────────────┘

  CLI:  main.py drives the pipeline directly on your machine.
  Web:  server.py exposes it over WebSocket; the Next.js app streams mic audio in and audio out.
```

| Stage | Component | Runs on |
| --- | --- | --- |
| Audio capture | `sounddevice` (CLI) / Web Audio API (browser) | CPU |
| Voice activity detection | Silero VAD | CPU |
| Speech-to-text | Groq `whisper-large-v3-turbo` | Cloud |
| Translation | Groq `llama-3.1-8b-instant` | Cloud |
| Text-to-speech | ElevenLabs (cloud) or Coqui XTTS-v2 (local CPU) | Cloud / CPU |

Stages are pipelined: one utterance is transcribed and translated while the previous one is still playing, which keeps end-to-end latency in the 1.5–2.5s range for short sentences.

## Project layout

```
.
├── main.py              Command-line interface
├── server.py            FastAPI WebSocket server for the web frontend
├── Dockerfile           Backend container for Render / Railway / Fly.io
├── requirements.txt
├── src/                 Shared pipeline used by both the CLI and the server
│   ├── config.py        Environment-based settings
│   ├── audio_capture.py Microphone capture and playback
│   ├── vad.py           Utterance segmentation
│   ├── stt.py           Speech-to-text
│   ├── translate.py     Translation
│   ├── tts.py           Text-to-speech backends
│   └── pipeline.py      CLI orchestrator
└── web/                 Next.js frontend (deploy to Vercel)
```

## Prerequisites

- Python 3.10+
- Node.js 18+ (only for the web frontend)
- A [Groq API key](https://console.groq.com) (free tier) for speech-to-text and translation
- An [ElevenLabs API key](https://elevenlabs.io) for cloud voice cloning (optional if you use the local XTTS backend)

## Setup

Install the CPU build of PyTorch first so the dependency resolver does not pull CUDA packages:

```bash
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
pip install -r requirements.txt
```

Create your environment file and fill in your keys:

```bash
cp .env.example .env
```

| Variable | Description | Default |
| --- | --- | --- |
| `GROQ_API_KEY` | Groq key for STT and translation | required |
| `ELEVENLABS_API_KEY` | ElevenLabs key for voice cloning | required for `elevenlabs` backend |
| `ELEVENLABS_VOICE_ID` | Cloned voice to synthesize with | required for `elevenlabs` backend |
| `SOURCE_LANG` | Language you speak | `en` |
| `TARGET_LANG` | Language to translate into | `es` |
| `TTS_BACKEND` | `elevenlabs` or `xtts` | `elevenlabs` |

## Usage

### Command line

Clone your voice once from a short sample (about 30 seconds of clean speech):

```bash
python main.py --clone "my-voice" voice_samples/me.wav
```

Copy the printed voice id into `ELEVENLABS_VOICE_ID`, then start translating:

```bash
python main.py
```

Speak, pause, and hear the translation in your voice. Press `Ctrl+C` to stop.

### Web app

Start the backend:

```bash
uvicorn server:app --host 0.0.0.0 --port 8000
```

Start the frontend in a second terminal:

```bash
cd web
npm install
cp .env.local.example .env.local   # set NEXT_PUBLIC_WS_URL=ws://localhost:8000/ws
npm run dev
```

Open http://localhost:3000 and press **Start talking**.

## Deployment

The frontend and backend deploy to different platforms because Vercel's serverless functions cannot hold the long-lived WebSocket connection the audio stream needs.

### Frontend on Vercel

1. Import the repository in Vercel and set the project root to `web/`.
2. Add the environment variable `NEXT_PUBLIC_WS_URL` pointing to your backend, for example `wss://your-backend.onrender.com/ws`.
3. Deploy.

A page served over HTTPS can only connect to a secure (`wss://`) WebSocket, so the backend must be reachable over TLS in production.

### Backend on Render / Railway / Fly.io

The included `Dockerfile` builds a CPU-only image and reads the port from `$PORT`. Set `GROQ_API_KEY`, `ELEVENLABS_API_KEY`, and `ELEVENLABS_VOICE_ID` as environment variables on the host. These platforms terminate TLS automatically, giving you the `wss://` endpoint the frontend expects.

## Security notes

- API keys are read from `.env` / host environment variables and are never committed; `.env` is git-ignored.
- CORS is open (`*`) for development convenience. Restrict `allow_origins` in `server.py` to your Vercel domain before exposing the backend publicly, otherwise anyone can drive your socket and consume your API credits.
- Groq's free tier is rate limited, and ElevenLabs bills per character of synthesized audio. Monitor usage for long-running sessions.

## Tuning latency

- Lower `silence_ms` in `src/vad.py` (default 600) to react faster, at the risk of cutting off slower speakers.
- Use the `elevenlabs` backend with the `eleven_turbo_v2_5` model (the default) for the lowest synthesis latency.
- The local `xtts` backend is free and offline but takes several seconds per sentence on CPU; use it for cost-free experimentation rather than live conversation.

## License

MIT
