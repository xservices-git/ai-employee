"use client";

import { useEffect, useState } from "react";
import { apiGet, apiDelete } from "@/lib/api";
import { Trash2, Shield } from "lucide-react";

type User = {
  id: string;
  email: string;
  name: string;
  role: "admin" | "approver" | "user";
  created_at: string;
};

const ROLE_STYLE: Record<string, string> = {
  admin: "bg-emerald-900/50 text-emerald-300 border-emerald-800",
  approver: "bg-amber-900/50 text-amber-300 border-amber-800",
  user: "bg-zinc-800 text-zinc-400 border-zinc-700",
};

export default function UsersPage() {
  const [users, setUsers] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function load() {
    setLoading(true);
    setError("");
    try {
      const d = await apiGet<{ items: User[] }>("/v1/auth/users");
      setUsers(d.items || []);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load users");
    } finally {
      setLoading(false);
    }
  }

  async function remove(id: string, name: string) {
    if (!confirm(`Delete user "${name}"? This cannot be undone.`)) return;
    try {
      await apiDelete(`/v1/auth/users/${id}`);
      await load();
    } catch (e) {
      alert(e instanceof Error ? e.message : "Delete failed");
    }
  }

  useEffect(() => {
    load();
  }, []);

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h2 className="text-xl font-semibold">Users ({users.length})</h2>
        <button
          onClick={load}
          disabled={loading}
          className="rounded border border-zinc-700 px-3 py-1 text-xs hover:bg-zinc-800"
        >
          {loading ? "Loading..." : "Refresh"}
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
              <th className="px-3 py-2">Name</th>
              <th className="px-3 py-2">Email</th>
              <th className="px-3 py-2">Role</th>
              <th className="px-3 py-2">Created</th>
              <th className="px-3 py-2"></th>
            </tr>
          </thead>
          <tbody>
            {users.map((u) => (
              <tr key={u.id} className="border-t border-zinc-800 hover:bg-zinc-900/50">
                <td className="px-3 py-2 font-medium">{u.name}</td>
                <td className="px-3 py-2 text-zinc-400">{u.email}</td>
                <td className="px-3 py-2">
                  <span
                    className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-xs ${
                      ROLE_STYLE[u.role] || ""
                    }`}
                  >
                    {u.role === "admin" && <Shield className="h-3 w-3" />}
                    {u.role}
                  </span>
                </td>
                <td className="px-3 py-2 text-xs text-zinc-500">
                  {new Date(u.created_at).toLocaleString()}
                </td>
                <td className="px-3 py-2 text-right">
                  <button
                    onClick={() => remove(u.id, u.name)}
                    className="rounded p-1 text-red-400 hover:bg-red-900/30"
                    title="Delete user"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </td>
              </tr>
            ))}
            {users.length === 0 && !loading && (
              <tr>
                <td colSpan={5} className="px-3 py-8 text-center text-zinc-500">
                  No users yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
}
