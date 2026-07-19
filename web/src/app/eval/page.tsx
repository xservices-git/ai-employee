"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, XCircle } from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";

type EvalStatus = {
  m1_status: string;
  task_types_supported: string[];
  mcp_servers: string[];
  test_count: number;
};

export default function EvalPage() {
  const [status, setStatus] = useState<EvalStatus | null>(null);
  const [result, setResult] = useState<unknown>(null);
  const [running, setRunning] = useState(false);

  async function load() {
    try {
      const s = await apiGet<EvalStatus>("/v1/eval/status");
      setStatus(s);
    } catch {
      // ignore
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function run() {
    setRunning(true);
    setResult(null);
    try {
      const r = await apiPost<unknown>("/v1/eval/run", {
        domain: "sales",
        ci_mode: false,
        fail_on_regression: false,
      });
      setResult(r);
    } catch (e) {
      setResult({ error: e instanceof Error ? e.message : "Failed" });
    } finally {
      setRunning(false);
    }
  }

  return (
    <div>
      <h2 className="mb-3 text-xl font-semibold">Eval Harness</h2>
      <div className="mb-4 grid grid-cols-2 gap-4">
        <div className="rounded border border-zinc-800 bg-zinc-900/30 p-4">
          <div className="text-sm text-zinc-400">M1 Status</div>
          <div className="mt-1 text-lg font-medium text-emerald-400">
            {status?.m1_status || "—"}
          </div>
        </div>
        <div className="rounded border border-zinc-800 bg-zinc-900/30 p-4">
          <div className="text-sm text-zinc-400">Task Types</div>
          <div className="mt-1 text-sm">
            {status?.task_types_supported?.length || 0} supported
          </div>
        </div>
        <div className="rounded border border-zinc-800 bg-zinc-900/30 p-4">
          <div className="text-sm text-zinc-400">Test Cases</div>
          <div className="mt-1 text-sm">{status?.test_count || 0} cases</div>
        </div>
        <div className="rounded border border-zinc-800 bg-zinc-900/30 p-4">
          <div className="text-sm text-zinc-400">MCP Servers</div>
          <div className="mt-1 text-sm">
            {status?.mcp_servers?.length || 0} configured
          </div>
        </div>
      </div>
      <div className="mb-4 rounded border border-zinc-800 bg-zinc-900/30 p-4">
        <div className="mb-2 text-sm text-zinc-400">Last result</div>
        <pre className="text-xs text-zinc-300">
          {result
            ? JSON.stringify(result, null, 2)
            : 'Run: cd D:\\picoclaw\\workspace\\ai-employee && python eval/eval_m1.py'}
        </pre>
      </div>
      <button
        onClick={run}
        disabled={running}
        className="rounded bg-emerald-600 px-4 py-2 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
      >
        {running ? "Running..." : "Run Eval"}
      </button>
    </div>
  );
}
