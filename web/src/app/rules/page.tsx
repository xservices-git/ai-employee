"use client";

import { useEffect, useState } from "react";
import { Check, X, Zap, AlertTriangle, ShieldCheck } from "lucide-react";
import { apiGet, apiPost } from "@/lib/api";

type Rule = {
  id: string;
  rule_text: string;
  condition_pattern: string | null;
  action_type: string | null;
  domain: string | null;
  evidence_count: number;
  success_count: number;
  fail_count: number;
  status: string;
  proposed_by: string;
  created_at: string;
  review_notes: string | null;
};

const STATUS_STYLE: Record<string, string> = {
  pending: "bg-amber-900/50 text-amber-300 border-amber-800",
  approved: "bg-emerald-900/50 text-emerald-300 border-emerald-800",
  rejected: "bg-zinc-800 text-zinc-400 border-zinc-700",
  auto_disabled: "bg-red-900/50 text-red-300 border-red-800",
};

export default function RulesPage() {
  const [filter, setFilter] = useState<string>("pending");
  const [items, setItems] = useState<Rule[]>([]);
  const [loading, setLoading] = useState(false);
  const [detecting, setDetecting] = useState(false);
  const [detectResult, setDetectResult] = useState<{
    patterns_found: number;
    rules_proposed: number;
    corrections_found: number;
  } | null>(null);

  async function load() {
    setLoading(true);
    try {
      const d = await apiGet<{ items: Rule[] }>(`/v1/rules?status=${filter}&limit=50`);
      setItems(d.items || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  async function decide(id: string, decision: "approved" | "rejected") {
    const notes = decision === "rejected" ? "Not relevant" : "Approved";
    await apiPost(`/v1/rules/${id}/decide`, { decision, review_notes: notes });
    await load();
  }

  async function detect() {
    setDetecting(true);
    setDetectResult(null);
    try {
      const r = await apiPost<typeof detectResult>(
        "/v1/rules/detect?min_occurrences=2",
        {}
      );
      setDetectResult(r);
      await load();
    } catch {
      // ignore
    } finally {
      setDetecting(false);
    }
  }

  useEffect(() => {
    load();
    const t = setInterval(load, 5000);
    return () => clearInterval(t);
  }, [filter]);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Proposed Rules (HUMAN GATE)</h2>
        <button
          onClick={detect}
          disabled={detecting}
          className="flex items-center gap-1 rounded bg-emerald-600 px-3 py-1.5 text-sm font-medium hover:bg-emerald-500 disabled:opacity-50"
        >
          <Zap className="h-4 w-4" />
          {detecting ? "Detecting..." : "Run Detection"}
        </button>
      </div>

      {detectResult && (
        <div className="mb-3 rounded border border-emerald-800 bg-emerald-950/50 p-3 text-sm">
          <ShieldCheck className="inline h-4 w-4" /> Detection:{" "}
          {detectResult.patterns_found} patterns, {detectResult.rules_proposed} rules
          proposed, {detectResult.corrections_found} corrections
        </div>
      )}

      <div className="mb-3 flex gap-1 text-sm">
        {["pending", "approved", "rejected", "auto_disabled"].map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={`rounded px-3 py-1 transition ${
              filter === s
                ? "bg-zinc-700 text-white"
                : "text-zinc-400 hover:bg-zinc-800"
            }`}
          >
            {s}
          </button>
        ))}
      </div>

      <div className="space-y-2">
        {items.map((r) => (
          <div key={r.id} className="rounded border border-zinc-800 bg-zinc-900/30 p-4">
            <div className="mb-2 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span
                  className={`rounded border px-2 py-0.5 text-xs font-medium ${
                    STATUS_STYLE[r.status] || ""
                  }`}
                >
                  {r.status}
                </span>
                {r.domain && <span className="text-xs text-zinc-400">[{r.domain}]</span>}
                <span className="text-xs text-zinc-500">by {r.proposed_by}</span>
              </div>
              {r.status === "pending" && (
                <div className="flex gap-2">
                  <button
                    onClick={() => decide(r.id, "approved")}
                    className="flex items-center gap-1 rounded bg-emerald-600 px-3 py-1 text-xs font-medium hover:bg-emerald-500"
                  >
                    <Check className="h-3 w-3" /> Approve
                  </button>
                  <button
                    onClick={() => decide(r.id, "rejected")}
                    className="flex items-center gap-1 rounded bg-red-600 px-3 py-1 text-xs font-medium hover:bg-red-500"
                  >
                    <X className="h-3 w-3" /> Reject
                  </button>
                </div>
              )}
            </div>
            <div className="text-sm text-zinc-200">{r.rule_text}</div>
            {r.condition_pattern && (
              <div className="mt-1 text-xs text-zinc-500">
                Pattern:{" "}
                <code className="rounded bg-zinc-800 px-1">{r.condition_pattern}</code>
              </div>
            )}
            <div className="mt-2 flex gap-4 text-xs text-zinc-500">
              <span>evidence: {r.evidence_count}</span>
              <span className="text-emerald-400">success: {r.success_count}</span>
              <span className="text-red-400">fail: {r.fail_count}</span>
              {r.success_count + r.fail_count > 0 && (
                <span>
                  rate:{" "}
                  {((r.success_count / (r.success_count + r.fail_count)) * 100).toFixed(0)}%
                </span>
              )}
              {r.review_notes && <span>notes: {r.review_notes}</span>}
            </div>
            {r.status === "auto_disabled" && (
              <div className="mt-2 flex items-center gap-1 text-xs text-red-400">
                <AlertTriangle className="h-3 w-3" /> Auto-disabled: success rate &lt; 50%
                over 20+ samples
              </div>
            )}
          </div>
        ))}
        {items.length === 0 && (
          <div className="rounded border border-zinc-800 bg-zinc-900/30 p-8 text-center text-zinc-500">
            No {filter} rules. {filter === "pending" && "Run detection to find patterns."}
          </div>
        )}
      </div>
    </div>
  );
}
