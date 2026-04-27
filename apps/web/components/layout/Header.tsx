"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3 } from "lucide-react";

const titles: Record<string, string> = {
  "/dashboard": "오늘 확인할 종목",
  "/analyze": "종목 분석",
  "/positions": "보유 종목",
  "/watchlist": "관심 종목",
  "/alerts": "가격 알림",
  "/settings": "설정"
};

export function Header() {
  const pathname = usePathname();
  return (
    <header className="sticky top-0 z-20 border-b border-border bg-appBg/95 px-5 py-4 backdrop-blur">
      <div className="mx-auto flex max-w-[480px] items-center justify-between">
        <Link href="/dashboard" className="flex items-center gap-2">
          <span className="flex h-9 w-9 items-center justify-center rounded-[8px] bg-primary text-white">
            <BarChart3 className="h-5 w-5" />
          </span>
          <span>
            <strong className="block text-lg leading-none text-text">StoPro</strong>
            <span className="text-xs font-medium text-subText">{titles[pathname] ?? "투자 분석"}</span>
          </span>
        </Link>
      </div>
    </header>
  );
}
