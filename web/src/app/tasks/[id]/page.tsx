"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Task = {
  id: string;
  status: string;
  input_data: { text?: string };
  plan: any;
  result: any;
  confidence: number | null;
  error_message: string | null;
  trace_id: string;
};
type Span = {
  name: string;
  duration_ms: number;
  status: string;
  attributes: any;
};

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [spans, setSpans] = useState<Span[]>([]);

  useEffect(() => {
    if (!id) return;
    const load = async () => {
      const r = await fetch(`${API}/v1/tasks/${id}`);
      const t = await r.json();
      setTask(t);
      const r2 = await fetch(`${API}/v1/tasks/${id}/trace`);
      const d = await r2.json();
      setSpans(d.spans || []);
    };
    load();
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [id]);

  if (!task) return <div className="text-zinc-500">Loading...</div>;

  return (
    <div>
      <Link href="/tasks" className="mb-4 inline-flex items-center gap-1 text-sm text-emerald-400 hover:underline">
        <ArrowLeft className="h-4 w-4" /> Tasks
      </Link>
      <h2 className="mb-2 text-xl font-semibold">Task #{task.id.slice(0, 8)}</h2>
      <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
        <div><span className="text-zinc-500">Status:</span> <span className="font-medium">{task.status}</span></div>
        <div><span className="text-zinc-500">Confidence:</span> {task.confidence != null ? (task.confidence * 100).toFixed(0) + "%" : "—"}</div>
        <div className="col-span-2"><span className="text-zinc-500">Input:</span> {task.input_data?.text}</div>
        {task.error_message && (
          <div className="col-span-2 text-red-400">Error: {task.error_message}</div>
        )}
      </div>

      <h3 className="mb-2 mt-6 text-sm font-semibold uppercase text-zinc-400">Plan</h3>
      <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-900/50 p-3 text-xs">
{JSON.stringify(task.plan, null, 2)}
      </pre>

      {task.result && (
        <>
          <h3 className="mb-2 mt-6 text-sm font-semibold uppercase text-zinc-400">Result</h3>
          <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-900/50 p-3 text-xs">
{JSON.stringify(task.result, null, 2)}
          </pre>
        </>
      )}

      <h3 className="mb-2 mt-6 text-sm font-semibold uppercase text-zinc-400">Trace ({spans.length} spans)</h3>
      <div className="space-y-2">
        {spans.map((s, i) => (
          <div key={i} className="flex items-center gap-3 rounded border border-zinc-800 bg-zinc-900/30 p-2 text-xs">
            <span className="w-32 font-mono text-zinc-400">{s.name}</span>
            <span className="text-zinc-500">{s.duration_ms}ms</span>
            <span className={s.status === "error" ? "text-red-400" : "text-emerald-400"}>{s.status}</span>
            {s.attributes && <span className="text-zinc-500 truncate">{JSON.stringify(s.attributes)}</span>}
          </div>
        ))}
      </div>
    </div>
  );
}
