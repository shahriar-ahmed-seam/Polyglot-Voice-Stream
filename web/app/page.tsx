"use client";

import { useRef, useState } from "react";
import { VoiceStream, type Result, type Status } from "@/lib/audio";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws";
const SOURCE_LANG = process.env.NEXT_PUBLIC_SOURCE_LANG ?? "EN";
const TARGET_LANG = process.env.NEXT_PUBLIC_TARGET_LANG ?? "ES";

const STATUS_LABEL: Record<Status, string> = {
  idle: "Ready",
  connecting: "Connecting",
  listening: "Listening",
  stopped: "Stopped",
  disconnected: "Disconnected",
  error: "Connection error",
};

export default function Home() {
  const [status, setStatus] = useState<Status>("idle");
  const [results, setResults] = useState<Result[]>([]);
  const streamRef = useRef<VoiceStream | null>(null);

  const live = status === "listening" || status === "connecting";

  const start = async () => {
    const stream = new VoiceStream(
      WS_URL,
      (r) => setResults((prev) => [r, ...prev]),
      setStatus
    );
    streamRef.current = stream;
    await stream.start();
  };

  const stop = () => {
    streamRef.current?.stop();
    streamRef.current = null;
  };

  const dotClass =
    status === "listening"
      ? "live"
      : status === "connecting"
      ? "connecting"
      : status === "error" || status === "disconnected"
      ? "error"
      : "";

  return (
    <div className="page">
      <header className="topbar">
        <div className="topbar-inner">
          <div className="brand">
            <span className="brand-mark" />
            Polyglot Voice Stream
          </div>
          <div className="status">
            <span className={`status-dot ${dotClass}`} />
            {STATUS_LABEL[status]}
          </div>
        </div>
      </header>

      <section className="hero">
        <div className="hero-inner">
          <span className="eyebrow">Real-time AI interpreter</span>
          <h1>
            Speak once. Be heard in <span className="grad">any language</span>,
            in your own voice.
          </h1>
          <p>
            Polyglot Voice Stream listens as you talk, translates on the fly, and
            speaks the result back in a clone of your voice — with end-to-end
            latency low enough for a real conversation.
          </p>

          <div className="controls">
            <button
              className={`btn ${live ? "btn-danger" : "btn-primary"}`}
              onClick={live ? stop : start}
            >
              {live ? "Stop session" : "Start talking"}
            </button>

            <div className="langpair">
              <span className="lang-chip">{SOURCE_LANG}</span>
              <span className="arrow">→</span>
              <span className="lang-chip">{TARGET_LANG}</span>
            </div>
          </div>
        </div>
      </section>

      <main className="content">
        <h2 className="section-label">Live transcript</h2>

        {results.length === 0 ? (
          <div className="empty">
            Press <strong>Start talking</strong> and say something. Your
            translations will appear here and play back automatically.
          </div>
        ) : (
          <ul className="feed">
            {results.map((r, i) => (
              <li className="card" key={i}>
                <div className="card-source">{r.source}</div>
                <div className="card-target">{r.target}</div>
                <span className="card-meta">{r.ms} ms</span>
              </li>
            ))}
          </ul>
        )}
      </main>
    </div>
  );
}
