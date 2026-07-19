"use client";

import { useEffect, useState } from "react";
import { apiGet } from "@/lib/api";
import { Globe, ChevronDown, ChevronRight, FileText } from "lucide-react";

type DomainInfo = {
  domain: string;
  config: Record<string, unknown>;
  rules: unknown[];
  rule_count: number;
};

export default function DomainsPage() {
  const [domains, setDomains] = useState<string[]>([]);
  const [selected, setSelected] = useState<DomainInfo | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingDetail, setLoadingDetail] = useState(false);
  const [expanded, setExpanded] = useState(false);

  async function load() {
    setLoading(true);
    try {
      const d = await apiGet<{ items: string[] }>("/v1/domains");
      setDomains(d.items || []);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }

  async function loadDomain(name: string) {
    setLoadingDetail(true);
    setExpanded(false);
    setSelected(null);
    try {
      const d = await apiGet<DomainInfo>(`/v1/domains/${name}`);
      setSelected(d);
    } catch {
      setSelected(null);
    } finally {
      setLoadingDetail(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <h2 className="mb-3 text-xl font-semibold">Domain Configurations</h2>

      <div className="grid grid-cols-[250px_1fr] gap-4">
        {/* Sidebar: domain list */}
        <div className="rounded border border-zinc-800 bg-zinc-900/50">
          <div className="border-b border-zinc-800 px-3 py-2 text-xs uppercase text-zinc-500">
            Domains ({domains.length})
          </div>
          <div className="space-y-0.5 p-2">
            {domains.map((d) => (
              <button
                key={d}
                onClick={() => loadDomain(d)}
                className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm text-zinc-300 hover:bg-zinc-800"
              >
                <Globe className="h-4 w-4 shrink-0 text-emerald-400" />
                {d}
              </button>
            ))}
            {domains.length === 0 && !loading && (
              <div className="px-3 py-8 text-center text-xs text-zinc-500">
                No domains configured.
              </div>
            )}
          </div>
        </div>

        {/* Detail pane */}
        <div className="rounded border border-zinc-800 bg-zinc-900/50 p-4">
          {loadingDetail && (
            <div className="text-center text-sm text-zinc-500">Loading...</div>
          )}
          {!loadingDetail && !selected && (
            <div className="text-center text-sm text-zinc-500">
              Select a domain to view config
            </div>
          )}
          {selected && !loadingDetail && (
            <div>
              <div className="mb-4 flex items-center justify-between">
                <h3 className="text-lg font-semibold text-zinc-100">
                  {selected.domain}
                </h3>
                <span className="rounded bg-zinc-800 px-2 py-0.5 text-xs text-zinc-400">
                  {selected.rule_count} rules
                </span>
              </div>

              {/* Config */}
              <div className="mb-4">
                <button
                  onClick={() => setExpanded(!expanded)}
                  className="mb-2 flex items-center gap-1 text-xs font-medium uppercase text-zinc-400 hover:text-zinc-200"
                >
                  {expanded ? (
                    <ChevronDown className="h-3 w-3" />
                  ) : (
                    <ChevronRight className="h-3 w-3" />
                  )}
                  Configuration
                </button>
                {expanded && (
                  <pre className="overflow-auto rounded border border-zinc-800 bg-zinc-950 p-3 text-xs text-zinc-300">
                    {JSON.stringify(selected.config, null, 2)}
                  </pre>
                )}
              </div>

              {/* Rules */}
              <div>
                <div className="mb-2 flex items-center gap-1 text-xs font-medium uppercase text-zinc-400">
                  <FileText className="h-3 w-3" />
                  Rules ({selected.rules.length})
                </div>
                <div className="space-y-2">
                  {selected.rules.length === 0 && (
                    <div className="text-xs text-zinc-500">No rules defined.</div>
                  )}
                  {selected.rules.map((rule: unknown, i: number) => (
                    <div
                      key={i}
                      className="rounded border border-zinc-800 bg-zinc-900/30 p-3"
                    >
                      <pre className="text-xs text-zinc-300">
                        {JSON.stringify(rule, null, 2)}
                      </pre>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
