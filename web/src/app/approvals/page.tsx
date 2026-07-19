"use client";

import { useEffect, useState } from "react";
import { Check, X } from "lucide-react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

type Approval = {
  id: string;
  task_id: string;
  risk_level: string;
  reason: string;
  proposal: any;
  created_at: string;
};

export default function ApprovalsPage() {
  const [items, setItems] = useState<Approval[]>([]);
  const [loading, setLoading] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const r = await fetch(`${API}/v1/approvals`);
      const d = await r.json();
      setItems(d.items || []);
    } finally {
      setLoading(false);
    }
  }

  async function decide(id: string, decision: "approved" | "rejected") {
    await fetch(`${API}/v1/approvals/${id}/decide`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ decision, feedback: "" }),
    });
    await load();
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 3000);
    return () => clearInterval(t);
  }, []);

  return (
    <div>
      <h2 className="mb-3 text-xl font-semibold">Pending Approvals ({items.length})</h2>
      <div className="space-y-3">
        {items.map((a) => (
          <div key={a.id} className="rounded border border-zinc-800 bg-zinc-900/30 p-4">
            <div className="mb-2 flex items-center justify-between">
              <div>
                <span className="text-sm font-medium">Approval #{a.id.slice(0, 8)}</span>
                <span className={`ml-2 rounded px-2 py-0.5 text-xs ${
                  a.risk_level === "high" ? "bg-red-900/50 text-red-300" :
                  a.risk_level === "medium" ? "bg-amber-900/50 text-amber-300" :
                  "bg-zinc-800 text-zinc-300"
                }`}>
                  {a.risk_level}
                </span>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => decide(a.id, "approved")}
                  className="rounded bg-emerald-600 px-3 py-1 text-xs font-medium hover:bg-emerald-500"
                >
                  <Check className="inline h-3 w-3" /> Approve
                </button>
                <button
                  onClick={() => decide(a.id, "rejected")}
                  className="rounded bg-red-600 px-3 py-1 text-xs font-medium hover:bg-red-500"
                >
                  <X className="inline h-3 w-3" /> Reject
                </button>
              </div>
            </div>
            <div className="text-xs text-zinc-500">Task: {a.task_id}</div>
            <div className="mt-1 text-sm text-zinc-400">{a.reason}</div>
            <pre className="mt-2 overflow-auto rounded bg-zinc-950 p-2 text-xs text-zinc-300">
{JSON.stringify(a.proposal, null, 2)}
            </pre>
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded border border-zinc-800 bg-zinc-900/30 p-8 text-center text-zinc-500">
            No pending approvals.
          </div>
        )}
      </div>
    </div>
  );
}
