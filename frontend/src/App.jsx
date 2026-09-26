import React, { useRef, useState } from "react";
import Heatmap from "./Heatmap.jsx";

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

const STARTER_PROMPTS = [
  "Cheapest week to Lisbon in the next month?",
  "Flex dates to Bangkok, roughly June",
  "Find me a cheap direct-ish trip to Athens",
];

export default function App() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      content:
        "Hi! I'm your Amsterdam Schiphol flex-date flight finder. Tell me a destination and how flexible you are on dates, and I'll map out prices day by day.",
    },
  ]);
  const [input, setInput] = useState("");
  const [heatmap, setHeatmap] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const listRef = useRef(null);

  async function send(text) {
    const message = (text ?? input).trim();
    if (!message || loading) return;

    const nextMessages = [...messages, { role: "user", content: message }];
    setMessages(nextMessages);
    setInput("");
    setLoading(true);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          history: nextMessages
            .filter((m) => m.role === "user" || m.role === "assistant")
            .slice(0, -1),
        }),
      });
      if (!res.ok) throw new Error(`Server error (${res.status})`);
      const data = await res.json();
      setMessages((m) => [...m, { role: "assistant", content: data.reply }]);
      if (data.heatmap) setHeatmap(data.heatmap);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
      requestAnimationFrame(() => {
        listRef.current?.scrollTo({ top: listRef.current.scrollHeight, behavior: "smooth" });
      });
    }
  }

  return (
    <div className="app">
      <header className="app-header">
        <div className="app-logo">✈️ AMS Flex-Date Finder</div>
        <div className="app-tagline">Conversational search, priced by the day, out of Amsterdam Schiphol.</div>
      </header>

      <main className="app-main">
        <section className="chat-panel">
          <div className="chat-list" ref={listRef}>
            {messages.map((m, i) => (
              <div key={i} className={`chat-bubble ${m.role}`}>
                {m.content}
              </div>
            ))}
            {loading && <div className="chat-bubble assistant loading">Searching flights…</div>}
            {error && <div className="chat-bubble error">⚠ {error}</div>}
          </div>

          <div className="chat-starters">
            {STARTER_PROMPTS.map((p) => (
              <button key={p} onClick={() => send(p)} disabled={loading}>
                {p}
              </button>
            ))}
          </div>

          <form
            className="chat-input"
            onSubmit={(e) => {
              e.preventDefault();
              send();
            }}
          >
            <input
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="e.g. Somewhere warm from AMS in the next 3 weeks?"
              disabled={loading}
            />
            <button type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
        </section>

        <section className="heatmap-panel">
          {heatmap ? (
            <Heatmap data={heatmap} />
          ) : (
            <div className="heatmap-placeholder">
              Your flex-date price heatmap will show up here once you ask about a destination.
            </div>
          )}
        </section>
      </main>
    </div>
  );
}
