"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Bell, BriefcaseBusiness, Home, LineChart, Search, Settings, Star } from "lucide-react";

const nav = [
  { href: "/dashboard", label: "홈", icon: Home },
  { href: "/analyze", label: "분석", icon: Search },
  { href: "/watchlist", label: "관심", icon: Star },
  { href: "/positions", label: "보유", icon: BriefcaseBusiness },
  { href: "/alerts", label: "알림", icon: Bell },
  { href: "/settings", label: "설정", icon: Settings }
];

export function BottomNav() {
  const pathname = usePathname();
  return (
    <nav className="fixed bottom-0 left-0 right-0 z-30 border-t border-border bg-white/95 backdrop-blur">
      <div className="mx-auto grid max-w-[480px] grid-cols-6 px-1 py-2">
        {nav.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={`flex min-h-12 flex-col items-center justify-center gap-1 rounded-[8px] text-[11px] font-bold ${active ? "text-primary" : "text-subText"}`}
              title={label}
            >
              <Icon className="h-5 w-5" />
              <span>{label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
