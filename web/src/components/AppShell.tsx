"use client";

import { usePathname, useRouter } from "next/navigation";
import { useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { Nav } from "@/components/nav";

// Public routes: no sidebar, no auth required.
const PUBLIC_ROUTES = new Set(["/login", "/register"]);

export function AppShell({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();
  const router = useRouter();
  const pathname = usePathname();
  const isPublic = PUBLIC_ROUTES.has(pathname);

  // Redirect to login if not authenticated and trying to access protected route
  useEffect(() => {
    if (loading) return;
    if (!user && !isPublic) {
      router.replace("/login");
    }
  }, [user, loading, isPublic, router]);

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-zinc-950 text-zinc-500">
        Loading...
      </div>
    );
  }

  // Public routes: render without shell
  if (isPublic || !user) {
    return <>{children}</>;
  }

  // Protected: render with sidebar
  return (
    <div className="flex min-h-screen">
      <Nav />
      <main className="flex-1 p-6">{children}</main>
    </div>
  );
}
