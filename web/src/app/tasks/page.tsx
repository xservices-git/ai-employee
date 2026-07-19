"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { RefreshCw } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Task = {
  id: string;
  task_type: string;
  domain: string | null;
  status: string;
  input_data: { text?: string };
  created_at: string;
  confidence: number | null;
};

const STATUS_COLOR: Record<string, string> = {
  pending: "text-zinc-400",
  running: "text-blue-400",
  waiting_approval: "text-amber-400",
  completed: "text-emerald-400",
  failed: "text-red-400",
  cancelled: "text-zinc-500",
};

export default function TasksPage() {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/v1/tasks?limit=50`);
      const data = await r.json();
      setTasks(data.items || []);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, []);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Tasks</h2>
        <button onClick={load} className="rounded p-2 hover:bg-zinc-800" title="Refresh">
          <RefreshCw className={`h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        </button>
      </div>
      <div className="overflow-hidden rounded border border-zinc-800">
        <table className="w-full text-sm">
          <thead className="bg-zinc-900 text-left text-xs uppercase text-zinc-400">
            <tr>
              <th className="px-3 py-2">ID</th>
              <th className="px-3 py-2">Type</th>
              <th className="px-3 py-2">Domain</th>
              <th className="px-3 py-2">Status</th>
              <th className="px-3 py-2">Confidence</th>
              <th className="px-3 py-2">Input</th>
              <th className="px-3 py-2">Created</th>
            </tr>
          </thead>
          <tbody>
            {tasks.map((t) => (
              <tr key={t.id} className="border-t border-zinc-800 hover:bg-zinc-900/50">
                <td className="px-3 py-2">
                  <Link href={`/tasks/${t.id}`} className="text-emerald-400 hover:underline">
                    {t.id.slice(0, 8)}
                  </Link>
                </td>
                <td className="px-3 py-2 font-mono text-xs">{t.task_type}</td>
                <td className="px-3 py-2 text-zinc-400">{t.domain || "—"}</td>
                <td className={`px-3 py-2 font-medium ${STATUS_COLOR[t.status] || "text-zinc-400"}`}>
                  {t.status}
                </td>
                <td className="px-3 py-2 text-zinc-400">
                  {t.confidence != null ? (t.confidence * 100).toFixed(0) + "%" : "—"}
                </td>
                <td className="px-3 py-2 text-zinc-300 max-w-xs truncate" title={t.input_data?.text}>
                  {t.input_data?.text?.slice(0, 50)}
                </td>
                <td className="px-3 py-2 text-xs text-zinc-500">
                  {new Date(t.created_at).toLocaleString()}
                </td>
              </tr>
            ))}
            {tasks.length === 0 && (
              <tr>
                <td colSpan={7} className="px-3 py-8 text-center text-zinc-500">
                  No tasks yet. Start chatting!
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
