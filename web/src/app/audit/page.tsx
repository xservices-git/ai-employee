"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { Search } from "lucide-react";

type AuditEntry = {
  id: number;
  ts: string;
  trace_id: string;
  actor: string;
  action: string;
  result: string;
  confidence: number | null;
  metadata: Record<string, unknown>;
};

const ACTION_STYLE: Record<string, string> = {
  register: "text-emerald-400",
  login: "text-blue-400",
  delete_user: "text-red-400",
  submit_feedback: "text-amber-400",
  approval_approved: "text-emerald-400",
  approval_rejected: "text-red-400",
  approval_modified: "text-amber-400",
  rule_approved: "text-emerald-400",
  rule_rejected: "text-red-400",
};

export default function AuditPage() {
  const [items, setItems] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [actorFilter, setActorFilter] = useState("");
  const [actionFilter, setActionFilter] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const params = new URLSearchParams({ limit: "200" });
      if (actorFilter) params.set("actor", actorFilter);
      if (actionFilter) params.set("action", actionFilter);
      const d = await apiGet<{ items: AuditEntry[] }>(`/v1/auth/audit?${params}`);
      setItems(d.items || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load audit log");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Audit Log ({items.length})</h2>
        <button
          onClick={load}
          disabled={loading}
          className="rounded border border-zinc-700 px-3 py-1 text-xs hover:bg-zinc-800"
        >
          {loading ? "Loading..." : "Refresh"}
        </button>
      </div>

      {/* Filters */}
      <div className="mb-3 flex gap-2">
        <input
          value={actorFilter}
          onChange={(e) => setActorFilter(e.target.value)}
          placeholder="Filter by actor..."
          className="flex-1 rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs focus:border-emerald-500 focus:outline-none"
        />
        <input
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          placeholder="Filter by action..."
          className="flex-1 rounded border border-zinc-700 bg-zinc-900 px-3 py-1.5 text-xs focus:border-emerald-500 focus:outline-none"
        />
        <button
          onClick={load}
          className="flex items-center gap-1 rounded bg-zinc-800 px-3 py-1.5 text-xs hover:bg-zinc-700"
        >
          <Search className="h-3 w-3" />
          Search
        </button>
      </div>

      {error && (
        <div className="mb-3 rounded bg-red-900/30 border border-red-800 px-3 py-2 text-sm text-red-300">
          {error}
        </div>
      )}

      <div className="overflow-hidden rounded border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900 text-left text-xs uppercase text-zinc-400">
            <tr>
              <th className="px-3 py-2">Time</th>
              <th className="px-3 py-2">Actor</th>
              <th className="px-3 py-2">Action</th>
              <th className="px-3 py-2">Result</th>
              <th className="px-3 py-2">Trace ID</th>
            </tr>
          </thead>
          <tbody>
            {items.map((e) => (
              <tr key={e.id} className="border-t border-zinc-800 hover:bg-zinc-900/50">
                <td className="px-3 py-2 text-xs text-zinc-500">
                  {new Date(e.ts).toLocaleString()}
                </td>
                <td className="px-3 py-2 font-mono text-xs">{e.actor}</td>
                <td className="px-3 py-2">
                  <span
                    className={`font-mono text-xs ${
                      ACTION_STYLE[e.action] || "text-zinc-300"
                    }`}
                  >
                    {e.action}
                  </span>
                </td>
                <td className="px-3 py-2">
                  <span
                    className={
                      e.result === "ok" ? "text-emerald-400" : "text-red-400"
                    }
                  >
                    {e.result}
                  </span>
                </td>
                <td className="px-3 py-2 font-mono text-[10px] text-zinc-500">
                  {e.trace_id ? e.trace_id.slice(0, 12) : "—"}
                </td>
              </tr>
            ))}
            {items.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-zinc-500">
                  No audit entries.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
