"use client";

import { useRef, useState } from "react";
import { VoiceStream, type Result } from "@/lib/audio";

const WS_URL = process.env.NEXT_PUBLIC_WS_URL ?? "ws://localhost:8000/ws";

export default function Home() {
  const [status, setStatus] = useState("idle");
  const [results, setResults] = useState<Result[]>([]);
  const streamRef = useRef<VoiceStream | null>(null);

  const start = async () => {
    const vs = new VoiceStream(
      WS_URL,
      (r) => setResults((prev) => [r, ...prev]),
      setStatus
    );
    streamRef.current = vs;
    await vs.start();
  };

  const stop = () => {
    streamRef.current?.stop();
    streamRef.current = null;
  };

  const live = status === "listening" || status === "connected";

  return (
    <main style={{ maxWidth: 640, margin: "40px auto", padding: 16 }}>
      <h1>Polyglot Voice Stream</h1>
      <p style={{ color: "#666" }}>
        Speak, and hear yourself translated. Status: <b>{status}</b>
      </p>

      <button
        onClick={live ? stop : start}
        style={{
          padding: "10px 20px",
          fontSize: 16,
          borderRadius: 8,
          border: "none",
          cursor: "pointer",
          background: live ? "#e11d48" : "#2563eb",
          color: "white",
        }}
      >
        {live ? "Stop" : "Start talking"}
      </button>

      <ul style={{ listStyle: "none", padding: 0, marginTop: 24 }}>
        {results.map((r, i) => (
          <li
            key={i}
            style={{ borderBottom: "1px solid #eee", padding: "12px 0" }}
          >
            <div style={{ color: "#888", fontSize: 14 }}>{r.source}</div>
            <div style={{ fontSize: 18 }}>{r.target}</div>
            <div style={{ color: "#bbb", fontSize: 12 }}>{r.ms} ms</div>
          </li>
        ))}
      </ul>
    </main>
  );
}
