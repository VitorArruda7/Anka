"use client";

import { Suspense, ReactNode, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Sidebar } from "@/components/layout/sidebar";
import { DashboardHeader } from "@/components/layout/header";
import { useAuth } from "@/hooks/use-auth";

export const dynamic = "force-dynamic";

function HeaderWithSuspense() {
  return (
    <Suspense fallback={null}>
      <DashboardHeader />
    </Suspense>
  );
}

export default function ProtectedLayout({ children }: { children: ReactNode }) {
  const { isAuthenticated, loading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.replace("/login");
    }
  }, [isAuthenticated, loading, router]);

  if (!isAuthenticated && !loading) {
    return null;
  }

  return (
    <div className="min-h-screen bg-background">
      <Sidebar />
      <main className="relative min-h-screen lg:ml-64">
        <div className="flex flex-col gap-6 p-6 lg:p-10">
          <HeaderWithSuspense />
          {children}
        </div>
      </main>
    </div>
  );
}
