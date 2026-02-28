"use client";

import { useState, useRef, useEffect, useCallback } from "react";

interface Message {
  role: "user" | "assistant";
  content: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputText, setInputText] = useState("");
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [speakingIdx, setSpeakingIdx] = useState<number | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = useCallback(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages, scrollToBottom]);

  const sendMessage = async () => {
    const text = inputText.trim();
    if (!text || isLoading) return;

    setInputText("");
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setIsLoading(true);

    try {
      const res = await fetch("/api/agent/text", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ sessionId, text }),
      });
      const data = await res.json();
      setSessionId(data.sessionId);
      setMessages((prev) => [...prev, { role: "assistant", content: data.reply }]);
    } catch (err) {
      setMessages((prev) => [
        ...prev,
        { role: "assistant", content: "Error: Failed to get response." },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const speakText = async (text: string, idx: number) => {
    if (speakingIdx !== null) return;
    setSpeakingIdx(idx);

    try {
      const res = await fetch("/api/agent/tts", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ text }),
      });
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audio.onended = () => {
        URL.revokeObjectURL(url);
        setSpeakingIdx(null);
      };
      audio.onerror = () => {
        URL.revokeObjectURL(url);
        setSpeakingIdx(null);
      };
      await audio.play();
    } catch {
      setSpeakingIdx(null);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chat-container">
      <header className="chat-header">
        <h1>Canard 🦆</h1>
        <span className="subtitle">Voice Agent</span>
      </header>

      <main className="messages-area">
        {messages.length === 0 && (
          <div className="empty-state">
            <p>👋 Send a message to start chatting with Canard</p>
          </div>
        )}
        {messages.map((msg, i) => (
          <div key={i} className={`message ${msg.role}`}>
            <div className="message-bubble">
              <p>{msg.content}</p>
              {msg.role === "assistant" && (
                <button
                  type="button"
                  className="speak-btn"
                  onClick={() => speakText(msg.content, i)}
                  disabled={speakingIdx !== null}
                >
                  {speakingIdx === i ? "🔊 Playing..." : "🔊 Speak"}
                </button>
              )}
            </div>
          </div>
        ))}
        {isLoading && (
          <div className="message assistant">
            <div className="message-bubble loading">
              <span className="dot" />
              <span className="dot" />
              <span className="dot" />
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </main>

      <footer className="input-area">
        <textarea
          value={inputText}
          onChange={(e) => setInputText(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a message..."
          rows={1}
          disabled={isLoading}
        />
        <button
          type="button"
          className="send-btn"
          onClick={sendMessage}
          disabled={isLoading || !inputText.trim()}
        >
          Send
        </button>
      </footer>
    </div>
  );
}
