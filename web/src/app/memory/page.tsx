"use client";

import { useState } from "react";
import { Search } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Episode = {
  id: string;
  task_id: string;
  task_type: string;
  domain: string | null;
  input_text: string;
  success: boolean;
  confidence: number | null;
  score: number;
};

export default function MemoryPage() {
  const [q, setQ] = useState("");
  const [results, setResults] = useState<Episode[]>([]);
  const [busy, setBusy] = useState(false);

  async function search() {
    if (!q.trim()) return;
    setBusy(true);
    try {
      const r = await fetch(`${API}/v1/memory/search`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query: q, top_k: 10 }),
      });
      const d = await r.json();
      setResults(d.results || []);
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <h2 className="mb-3 text-xl font-semibold">Memory Search</h2>
      <div className="mb-4 flex gap-2">
        <input
          value={q}
          onChange={(e) => setQ(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="Search episodes..."
          className="flex-1 rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
        />
        <button
          onClick={search}
          disabled={busy}
          className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          <Search className="h-4 w-4" />
        </button>
      </div>
      <div className="space-y-2">
        {results.map((r) => (
          <div key={r.id} className="rounded border border-zinc-800 bg-zinc-900/30 p-3 text-sm">
            <div className="mb-1 flex items-center gap-2 text-xs">
              <span className="rounded bg-zinc-800 px-2 py-0.5 font-mono">{r.task_type}</span>
              {r.domain && <span className="text-zinc-400">{r.domain}</span>}
              <span className={r.success ? "text-emerald-400" : "text-red-400"}>
                {r.success ? "ok" : "fail"}
              </span>
              <span className="ml-auto text-zinc-500">score={r.score}</span>
            </div>
            <div className="text-zinc-300">{r.input_text}</div>
          </div>
        ))}
        {results.length === 0 && q && !busy && (
          <div className="text-center text-sm text-zinc-500">No matches.</div>
        )}
      </div>
    </div>
  );
}
