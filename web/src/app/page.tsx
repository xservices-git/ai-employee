"use client";

import { useState, useRef, useEffect } from "react";
import { Send, Bot, User } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Msg = { role: "user" | "assistant"; text: string; taskId?: string; status?: string };

export default function ChatPage() {
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<Msg[]>([]);
  const [busy, setBusy] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send() {
    if (!input.trim() || busy) return;
    const text = input.trim();
    setInput("");
    setMessages((m) => [...m, { role: "user", text }]);
    setBusy(true);
    try {
      const r = await fetch(`${API}/v1/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input: text, auto_run: true }),
      });
      const task = await r.json();
      setMessages((m) => [
        ...m,
        { role: "assistant", text: `Tao task #${task.id.slice(0, 8)} (${task.status})`, taskId: task.id, status: task.status },
      ]);
      // Poll status
      let attempts = 0;
      const poll = setInterval(async () => {
        attempts++;
        try {
          const r2 = await fetch(`${API}/v1/tasks/${task.id}`);
          const t = await r2.json();
          setMessages((m) =>
            m.map((msg) => (msg.taskId === task.id ? { ...msg, status: t.status } : msg))
          );
          if (["completed", "failed", "cancelled", "waiting_approval"].includes(t.status) || attempts > 20) {
            clearInterval(poll);
            if (t.result) {
              setMessages((m) => [
                ...m,
                { role: "assistant", text: JSON.stringify(t.result, null, 2) },
              ]);
            } else if (t.error_message) {
              setMessages((m) => [...m, { role: "assistant", text: `Error: ${t.error_message}` }]);
            }
          }
        } catch {
          clearInterval(poll);
        }
      }, 1000);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: `Network error: ${e}` }]);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-[calc(100vh-3rem)] flex-col">
      <h2 className="mb-3 text-xl font-semibold">Chat</h2>
      <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto rounded border border-zinc-800 bg-zinc-900/30 p-4">
        {messages.length === 0 && (
          <div className="text-center text-sm text-zinc-500">
            Gui yeu cau (tieng Viet) - AI se tu phan loai + plan + execute.
            <br />
            Vi du: &quot;Kiem tra don hang #12345&quot;, &quot;Viet email chao khach&quot;
          </div>
        )}
        {messages.map((m, i) => (
          <div key={i} className={`flex gap-2 ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            {m.role === "assistant" && <Bot className="h-6 w-6 shrink-0 text-emerald-400" />}
            <div
              className={`max-w-[80%] rounded-lg px-3 py-2 text-sm ${
                m.role === "user"
                  ? "bg-emerald-600/20 text-emerald-100"
                  : "bg-zinc-800 text-zinc-200"
              }`}
            >
              <pre className="whitespace-pre-wrap font-sans">{m.text}</pre>
              {m.taskId && (
                <a
                  href={`/tasks/${m.taskId}`}
                  className="mt-1 inline-block text-xs text-emerald-400 hover:underline"
                >
                  View task #{m.taskId.slice(0, 8)} ({m.status})
                </a>
              )}
            </div>
            {m.role === "user" && <User className="h-6 w-6 shrink-0 text-zinc-500" />}
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-2">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          placeholder="Nhap yeu cau..."
          className="flex-1 rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
          disabled={busy}
        />
        <button
          onClick={send}
          disabled={busy || !input.trim()}
          className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-500 disabled:opacity-50"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
