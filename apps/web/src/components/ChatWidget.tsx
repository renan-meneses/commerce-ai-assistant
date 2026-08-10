import { useState } from 'react';
import { api } from '../api/client';
import type { AiChatMessage } from '../api/types';

export default function ChatWidget() {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState<AiChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const send = async () => {
    const content = input.trim();
    if (!content || busy) return;
    setInput('');
    setError(null);
    const next = [...messages, { role: 'user' as const, content }];
    setMessages(next);
    setBusy(true);
    try {
      const response = await api.aiChat({ messages: next });
      setMessages((m) => [
        ...m,
        { role: 'assistant', content: response.answer },
      ]);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'AI service unavailable');
      setMessages((m) => m.slice(0, -1));
    } finally {
      setBusy(false);
    }
  };

  if (!open) {
    return (
      <button className="chat-toggle" onClick={() => setOpen(true)} aria-label="Open AI assistant">
        ✦
      </button>
    );
  }

  return (
    <div className="chat-widget">
      <div className="chat-header">
        Shopping Assistant
        <button
          className="btn"
          style={{ float: 'right', padding: '0.1rem 0.5rem' }}
          onClick={() => setOpen(false)}
        >
          ✕
        </button>
      </div>
      <div className="chat-messages">
        {messages.length === 0 && (
          <div className="chat-msg assistant">
            Hi! Ask me about products, prices, stock or orders — for example: "Which
            notebook with 16 GB RAM is good for Docker under R$5.000?"
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`chat-msg ${m.role}`}>
            {m.content}
          </div>
        ))}
        {busy && <div className="chat-msg assistant">Thinking…</div>}
        {error && <div className="chat-msg assistant">{error}</div>}
      </div>
      <div className="chat-input">
        <input
          className="input"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && send()}
          placeholder="Ask about products, prices, stock…"
        />
        <button className="btn btn-primary" onClick={send} disabled={busy}>
          Send
        </button>
      </div>
    </div>
  );
}
