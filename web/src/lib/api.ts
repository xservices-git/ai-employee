// API client with JWT token.
// Replaces all raw fetch() calls. Handles auth headers + 401 redirect.

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("ai_employee_token");
}

export async function api<T = unknown>(
  path: string,
  opts: RequestInit = {}
): Promise<T> {
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(opts.headers as Record<string, string>),
  };
  const token = getToken();
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }
  const r = await fetch(`${API_BASE}${path}`, { ...opts, headers });
  if (r.status === 401 && typeof window !== "undefined") {
    localStorage.removeItem("ai_employee_token");
    localStorage.removeItem("ai_employee_user");
    window.location.href = "/login";
    throw new Error("Unauthorized");
  }
  if (!r.ok) {
    const body = await r.json().catch(() => ({ detail: `HTTP ${r.status}` }));
    throw new Error(body.detail || body.message || `HTTP ${r.status}`);
  }
  if (r.status === 204) return undefined as T;
  return r.json();
}

// Convenience methods
export const apiGet = <T = unknown>(path: string) => api<T>(path);
export const apiPost = <T = unknown>(path: string, body: unknown) =>
  api<T>(path, { method: "POST", body: JSON.stringify(body) });
export const apiPatch = <T = unknown>(path: string, body: unknown) =>
  api<T>(path, { method: "PATCH", body: JSON.stringify(body) });
export const apiDelete = <T = unknown>(path: string) =>
  api<T>(path, { method: "DELETE" });
