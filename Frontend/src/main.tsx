import React, { useState } from "react";
import { createRoot } from "react-dom/client";
import "./index.css";

type Msg = {
  role: "user" | "assistant";
  content: string;
};

const API_BASE = "https://education-chatbot-production.up.railway.app";

export default function App() {
  const [messages, setMessages] = useState<Msg[]>([
    {
      role: "assistant",
      content:
        "Hello. I am your education knowledge assistant. Upload your research and ask me questions."
    }
  ]);
  const [text, setText] = useState("");
  const [uploading, setUploading] = useState(false);
  const [thinking, setThinking] = useState(false);
  const [status, setStatus] = useState("");

  async function handleUpload(files: FileList | null) {
    if (!files || files.length === 0) return;

    const formData = new FormData();
    formData.append("file", files[0]);

    setUploading(true);
    setStatus("Uploading knowledge files...");

    try {
      const res = await fetch(`${API_BASE}/upload`, {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Upload failed");

      setStatus(`Uploaded ${data.uploaded.length} file(s) successfully.`);
    } catch (error: any) {
      setStatus(`Upload error: ${error.message}`);
    } finally {
      setUploading(false);
    }
  }

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
        <h1>Dr. Kaisa</h1>
        <p className="subtitle">Let's chat.</p>

        <div className="toolbar">
          <label className="upload-btn">
            {uploading ? "Uploading..." : "Upload research files"}
            <input
              type="file"
              multiple
              onChange={(e) => handleUpload(e.target.files)}
              hidden
            />
          </label>
          <span className="status">{status}</span>
        </div>

        <div className="chatbox">
          {messages.map((m, i) => (
            <div
              key={i}
              className={`msg ${m.role === "user" ? "user" : "assistant"}`}
            >
              <div className="role">{m.role === "user" ? "You" : "Assistant"}</div>
              <div>{m.content}</div>
            </div>
          ))}
          {thinking && <div className="thinking">Thinking...</div>}
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