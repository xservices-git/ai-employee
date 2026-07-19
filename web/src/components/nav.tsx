"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useAuth } from "@/contexts/AuthContext";
import {
  Bot,
  ListTodo,
  ShieldCheck,
  MemoryStick,
  BarChart3,
  BookCheck,
  Globe,
  FileText,
  Users,
  LogOut,
} from "lucide-react";

const links = [
  { href: "/", label: "Chat", icon: Bot },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/approvals", label: "Approvals", icon: ShieldCheck },
  { href: "/rules", label: "Rules", icon: BookCheck },
  { href: "/memory", label: "Memory", icon: MemoryStick },
  { href: "/eval", label: "Eval", icon: BarChart3 },
];

const adminLinks = [
  { href: "/users", label: "Users", icon: Users },
  { href: "/audit", label: "Audit Log", icon: FileText },
  { href: "/domains", label: "Domains", icon: Globe },
];

const ROLE_BADGE: Record<string, string> = {
  admin: "bg-emerald-900/50 text-emerald-300 border-emerald-800",
  approver: "bg-amber-900/50 text-amber-300 border-amber-800",
  user: "bg-zinc-800 text-zinc-400 border-zinc-700",
};

export function Nav() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="flex w-56 flex-col border-r border-zinc-800 bg-zinc-900/50 p-4">
      <h1 className="mb-6 text-lg font-semibold text-zinc-100">AI Employee</h1>

      <nav className="space-y-1 flex-1">
        {links.map((l) => {
          const Icon = l.icon;
          const active = pathname === l.href;
          return (
            <Link
              key={l.href}
              href={l.href}
              className={`flex items-center gap-2 rounded px-3 py-2 text-sm transition ${
                active
                  ? "bg-zinc-800 text-white"
                  : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100"
              }`}
            >
              <Icon className="h-4 w-4" />
              {l.label}
            </Link>
          );
        })}

        {/* Admin section */}
        {user?.role === "admin" && (
          <>
            <div className="my-3 border-t border-zinc-800" />
            <div className="px-3 pb-1 text-xs uppercase text-zinc-600">Admin</div>
            {adminLinks.map((l) => {
              const Icon = l.icon;
              const active = pathname === l.href;
              return (
                <Link
                  key={l.href}
                  href={l.href}
                  className={`flex items-center gap-2 rounded px-3 py-2 text-sm transition ${
                    active
                      ? "bg-zinc-800 text-white"
                      : "text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100"
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {l.label}
                </Link>
              );
            })}
          </>
        )}
      </nav>

      {/* User section */}
      {user && (
        <div className="mt-4 border-t border-zinc-800 pt-4">
          <div className="mb-2 flex items-center justify-between">
            <span className="truncate text-xs text-zinc-300">{user.name}</span>
            <span
              className={`rounded border px-1.5 py-0.5 text-[10px] font-medium ${
                ROLE_BADGE[user.role] || ""
              }`}
            >
              {user.role}
            </span>
          </div>
          <div className="mb-2 truncate text-xs text-zinc-500">{user.email}</div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded px-3 py-1.5 text-xs text-zinc-400 hover:bg-zinc-800/50 hover:text-zinc-100"
          >
            <LogOut className="h-3 w-3" />
            Logout
          </button>
        </div>
      )}

      <div className="mt-4 text-xs text-zinc-600">
        <div>v0.1.0</div>
      </div>
    </aside>
  );
}
