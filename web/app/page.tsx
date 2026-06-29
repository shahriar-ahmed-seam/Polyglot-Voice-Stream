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
      <section className="hero">
        <nav className="nav container">
          <div className="brand">
            <span className="brand-mark" />
            Polyglot Voice Stream
          </div>
          <div className="status">
            <span className={`status-dot ${dotClass}`} />
            {STATUS_LABEL[status]}
          </div>
        </nav>

        <div className="hero-body container">
          <span className="kicker">Real-time AI interpreter</span>
          <h1>
            Speak once.
            <br />
            Be heard in <em>any language</em>.
          </h1>
          <p className="lede">
            Polyglot listens as you talk, translates on the fly, and speaks the
            result back in a clone of your own voice — fast enough to hold a real
            conversation across borders.
          </p>

          <div className="actions">
            <button
              className={`btn ${live ? "btn-stop" : "btn-primary"}`}
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

      <main className="content container">
        <div className="content-head">
          <h2>Live transcript</h2>
          <span className="count">
            {results.length === 0 ? "Awaiting input" : `${results.length} translated`}
          </span>
        </div>

        {results.length === 0 ? (
          <div className="empty">
            Press <strong>Start talking</strong> and say something. Each phrase you
            speak appears here translated, and plays back in your voice.
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

      <footer className="footer container">
        <span>Polyglot Voice Stream</span>
        <span>
          {SOURCE_LANG} → {TARGET_LANG}
        </span>
      </footer>
    </div>
  );
}
