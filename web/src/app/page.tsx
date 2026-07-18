"use client";

import { useState } from "react";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

interface Task {
  id: string;
  status: string;
  task_type?: string;
  domain?: string;
  confidence?: { final?: number; familiarity?: number; clarity?: number; risk?: number; similarity?: number; simplicity?: number };
  result?: Record<string, unknown>;
  error_message?: string;
}

export default function Home() {
  const [input, setInput] = useState("");
  const [task, setTask] = useState<Task | null>(null);
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!input.trim()) return;
    setLoading(true);
    setTask(null);
    try {
      const r = await fetch(`${API_URL}/v1/tasks`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input, user_id: "demo_user" }),
      });
      const data = await r.json();
      setTask(data);
    } catch (e) {
      setTask({ id: "error", status: "failed", error_message: String(e) });
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="mx-auto max-w-3xl p-6">
      <h1 className="mb-2 text-3xl font-bold">AI Employee V3.0</h1>
      <p className="mb-6 text-gray-600">Local multi-agent AI assistant</p>

      <div className="mb-4 flex gap-2">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && submit()}
          placeholder="Nhập yêu cầu của bạn..."
          className="flex-1 rounded border border-gray-300 px-3 py-2 focus:border-brand-500 focus:outline-none"
        />
        <button
          onClick={submit}
          disabled={loading}
          className="rounded bg-brand-500 px-4 py-2 text-white hover:bg-brand-600 disabled:opacity-50"
        >
          {loading ? "Đang xử lý..." : "Gửi"}
        </button>
      </div>

      {task && (
        <div className="rounded border bg-white p-4 shadow-sm">
          <div className="mb-2 flex items-center gap-2">
            <span className="text-sm text-gray-500">Status:</span>
            <span
              className={`rounded px-2 py-0.5 text-xs ${
                task.status === "completed"
                  ? "bg-green-100 text-green-700"
                  : task.status === "failed"
                    ? "bg-red-100 text-red-700"
                    : "bg-yellow-100 text-yellow-700"
              }`}
            >
              {task.status}
            </span>
            {task.task_type && (
              <span className="rounded bg-blue-100 px-2 py-0.5 text-xs text-blue-700">
                {task.task_type}
              </span>
            )}
            {task.confidence && task.confidence.final !== undefined && (
              <span className="rounded bg-purple-100 px-2 py-0.5 text-xs text-purple-700">
                conf: {(task.confidence.final * 100).toFixed(0)}%
              </span>
            )}
          </div>

          {task.error_message && (
            <div className="mt-2 text-red-600">Error: {task.error_message}</div>
          )}

          {task.result && (
            <pre className="mt-3 overflow-x-auto rounded bg-gray-50 p-3 text-sm">
              {JSON.stringify(task.result, null, 2)}
            </pre>
          )}
        </div>
      )}
    </main>
  );
}
