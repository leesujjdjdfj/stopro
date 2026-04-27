import type { ReactNode } from "react";
import { Header } from "@/components/layout/Header";
import { BottomNav } from "@/components/layout/BottomNav";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto min-h-[calc(100vh-76px)] max-w-[480px] bg-appBg px-4 pb-28 pt-4 shadow-[0_0_40px_rgba(15,23,42,0.08)]">
        {children}
      </main>
      <BottomNav />
    </div>
  );
}
