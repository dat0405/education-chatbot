import React, { useEffect, useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

type Msg = {
  role: "user" | "assistant";
  content: string;
};

const API_BASE = "https://education-chatbot-production.up.railway.app";
const STORAGE_KEY = "chat_messages";

const DEFAULT_MESSAGES: Msg[] = [
  {
    role: "assistant",
    content: "Hello. I’m Dr. AI Kaisa. How can I help you today?"
  }
];

function App() {
  const [messages, setMessages] = useState<Msg[]>(() => {
    const saved = localStorage.getItem(STORAGE_KEY);

    if (saved) {
      try {
        return JSON.parse(saved);
      } catch {
        return DEFAULT_MESSAGES;
      }
    }

    return DEFAULT_MESSAGES;
  });

  const [text, setText] = useState("");
  const [thinking, setThinking] = useState(false);

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(messages));
  }, [messages]);

  async function sendMessage(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || thinking) return;

    const next = [...messages, { role: "user" as const, content: text }];
    setMessages(next);
    setText("");
    setThinking(true);

    try {
      const res = await fetch(`${API_BASE}/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify({ messages: next })
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Chat failed");

      setMessages([...next, { role: "assistant", content: data.answer }]);
    } catch (error: any) {
      setMessages([
        ...next,
        { role: "assistant", content: `Error: ${error.message}` }
      ]);
    } finally {
      setThinking(false);
    }
  }

  return (
    <div className="page">
      <div className="container">
        <header className="hero">
          <img
            src="/kaisa-logo.png"
            alt="Dr. AI Kaisa logo"
            className="kaisa-logo"
          />

          <div className="hero-text">
            <h1>Dr. AI KAISA</h1>
            <p className="subtitle">Let’s chat</p>
          </div>
        </header>

        <div className="chatbox">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`message-row ${
                m.role === "user" ? "user-row" : "assistant-row"
              }`}
            >
              {m.role === "assistant" && (
                <img
                  src="/kaisa-logo.png"
                  alt="Dr. AI Kaisa avatar"
                  className="chat-avatar assistant-avatar"
                />
              )}

              <div className={`msg ${m.role === "user" ? "user" : "assistant"}`}>
                <div className="role">
                  {m.role === "user" ? "You" : "Dr. AI Kaisa"}
                </div>
                <div>{m.content}</div>
              </div>

              {m.role === "user" && (
                <img
                  src="/ai-avatar.svg"
                  alt="User avatar"
                  className="chat-avatar user-avatar"
                />
              )}
            </div>
          ))}

          {thinking && (
            <div className="message-row assistant-row">
              <img
                src="/kaisa-logo.png"
                alt="Dr. AI Kaisa avatar"
                className="chat-avatar assistant-avatar"
              />
              <div className="thinking">Thinking...</div>
            </div>
          )}
        </div>

        <form className="composer" onSubmit={sendMessage}>
          <input
            value={text}
            onChange={(e) => setText(e.target.value)}
            placeholder="Ask a question about your research or educational approach..."
          />
          <button type="submit">Send</button>
        </form>
      </div>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);