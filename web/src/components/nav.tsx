"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bot, ListTodo, ShieldCheck, MemoryStick, BarChart3 } from "lucide-react";

const links = [
  { href: "/", label: "Chat", icon: Bot },
  { href: "/tasks", label: "Tasks", icon: ListTodo },
  { href: "/approvals", label: "Approvals", icon: ShieldCheck },
  { href: "/memory", label: "Memory", icon: MemoryStick },
  { href: "/eval", label: "Eval", icon: BarChart3 },
];

export function Nav() {
  const pathname = usePathname();
  return (
    <aside className="w-56 border-r border-zinc-800 bg-zinc-900/50 p-4">
      <h1 className="mb-6 text-lg font-semibold text-zinc-100">AI Employee</h1>
      <nav className="space-y-1">
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
      </nav>
      <div className="mt-8 text-xs text-zinc-600">
        <div>v0.1.0</div>
        <div>1 orchestrator</div>
        <div>3 memory tang</div>
      </div>
    </aside>
  );
}
