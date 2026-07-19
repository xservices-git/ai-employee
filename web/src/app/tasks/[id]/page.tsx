"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Send, CheckCircle2, AlertCircle } from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";

type Task = {
  id: string;
  status: string;
  input_data: { text?: string };
  plan: unknown;
  result: unknown;
  confidence: number | null;
  error_message: string | null;
  trace_id: string;
};
type Span = {
  name: string;
  duration_ms: number;
  status: string;
  attributes: unknown;
};
type Feedback = {
  id: string;
  score: number;
  notes: string | null;
  created_at: string;
};

export default function TaskDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [task, setTask] = useState<Task | null>(null);
  const [spans, setSpans] = useState<Span[]>([]);
  const [feedback, setFeedback] = useState<Feedback[]>([]);
  const [score, setScore] = useState(5);
  const [notes, setNotes] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  async function load() {
    if (!id) return;
    try {
      const t = await apiGet<Task>(`/v1/tasks/${id}`);
      setTask(t);
      const d = await apiGet<{ spans: Span[] }>(`/v1/tasks/${id}/trace`);
      setSpans(d.spans || []);
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 2000);
    return () => clearInterval(t);
  }, [id]);

  async function submitFeedback() {
    setSubmitting(true);
    try {
      await apiPost(`/v1/tasks/${id}/feedback`, {
        score,
        notes: notes || null,
      });
      setSubmitted(true);
      setNotes("");
      setTimeout(() => setSubmitted(false), 2000);
    } catch {
      // ignore
    } finally {
      setSubmitting(false);
    }
  }

  if (!task) return <div className="text-zinc-500">Loading...</div>;

  const isFinal = ["completed", "failed", "cancelled"].includes(task.status);

  return (
    <div>
      <Link
        href="/tasks"
        className="mb-4 inline-flex items-center gap-1 text-sm text-emerald-400 hover:underline"
      >
        <ArrowLeft className="h-4 w-4" /> Tasks
      </Link>
      <h2 className="mb-2 text-xl font-semibold">Task #{task.id.slice(0, 8)}</h2>
      <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
        <div>
          <span className="text-zinc-500">Status:</span>{" "}
          <span className="font-medium">{task.status}</span>
        </div>
        <div>
          <span className="text-zinc-500">Confidence:</span>{" "}
          {task.confidence != null ? (task.confidence * 100).toFixed(0) + "%" : "—"}
        </div>
        <div className="col-span-2">
          <span className="text-zinc-500">Input:</span> {task.input_data?.text}
        </div>
        {task.error_message && (
          <div className="col-span-2 text-red-400">Error: {task.error_message}</div>
        )}
      </div>

      {isFinal && (
        <div className="mb-6 rounded border border-zinc-800 bg-zinc-900/30 p-4">
          <h3 className="mb-2 text-sm font-semibold uppercase text-zinc-400">Feedback</h3>
          {submitted ? (
            <div className="flex items-center gap-1 text-sm text-emerald-400">
              <CheckCircle2 className="h-4 w-4" /> Da gui feedback
            </div>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-sm text-zinc-400">Score:</span>
                {[1, 2, 3, 4, 5].map((n) => (
                  <button
                    key={n}
                    onClick={() => setScore(n)}
                    className={`rounded px-3 py-1 text-sm ${
                      score === n
                        ? n >= 4
                          ? "bg-emerald-600 text-white"
                          : n >= 3
                            ? "bg-amber-600 text-white"
                            : "bg-red-600 text-white"
                        : "bg-zinc-800 text-zinc-300 hover:bg-zinc-700"
                    }`}
                  >
                    {n}
                  </button>
                ))}
              </div>
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                placeholder="Notes (optional) - what was wrong, suggestions..."
                className="w-full rounded border border-zinc-700 bg-zinc-900 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none"
                rows={2}
              />
              <button
                onClick={submitFeedback}
                disabled={submitting}
                className="flex items-center gap-1 rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
              >
                <Send className="h-3 w-3" /> Submit
              </button>
            </div>
          )}
          {feedback.length > 0 && (
            <div className="mt-3 border-t border-zinc-800 pt-2">
              <div className="text-xs text-zinc-500">Previous feedback:</div>
              {feedback.map((f) => (
                <div key={f.id} className="mt-1 text-xs text-zinc-400">
                  Score {f.score}/5 {f.notes && `- ${f.notes}`}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      <h3 className="mb-2 text-sm font-semibold uppercase text-zinc-400">Plan</h3>
      <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-900/50 p-3 text-xs">
        {JSON.stringify(task.plan, null, 2)}
      </pre>

      {task.result != null && (
        <>
          <h3 className="mb-2 mt-6 text-sm font-semibold uppercase text-zinc-400">Result</h3>
          <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-900/50 p-3 text-xs">
            {JSON.stringify(task.result, null, 2)}
          </pre>
        </>
      )}

      <h3 className="mb-2 mt-6 text-sm font-semibold uppercase text-zinc-400">
        Trace ({spans.length} spans)
      </h3>
      <div className="space-y-2">
        {spans.map((s, i) => (
          <div
            key={i}
            className="flex items-center gap-3 rounded border border-zinc-800 bg-zinc-900/30 p-2 text-xs"
          >
            <span className="w-32 font-mono text-zinc-400">{s.name}</span>
            <span className="text-zinc-500">{s.duration_ms}ms</span>
            <span className={s.status === "error" ? "text-red-400" : "text-emerald-400"}>
              {s.status}
            </span>
            {s.attributes != null && (
              <span className="truncate text-zinc-500">{JSON.stringify(s.attributes)}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
