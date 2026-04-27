"use client";

import { useCallback, useEffect, useState } from "react";
import Link from "next/link";
import { ArrowRight, BriefcaseBusiness, Search, Star } from "lucide-react";
import { Button } from "@/components/common/Button";
import { DisclaimerBanner } from "@/components/common/DisclaimerBanner";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { CandidateCard } from "@/components/dashboard/CandidateCard";
import { RiskAlertList } from "@/components/dashboard/RiskAlertList";
import { TodaySummaryCard } from "@/components/dashboard/TodaySummaryCard";
import { WatchlistSignalTable } from "@/components/dashboard/WatchlistSignalTable";
import { api } from "@/lib/api";
import { EXAMPLE_TICKERS } from "@/lib/constants";
import type { DashboardResponse } from "@/types/analysis";

export default function DashboardPage() {
  const [data, setData] = useState<DashboardResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setData(await api.dashboard());
    } catch (err) {
      setError(err instanceof Error ? err.message : "대시보드를 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const addExample = async (ticker: string) => {
    await api.addWatchlist({ ticker, note: "예시 관심종목" });
    await load();
  };

  if (loading) return <LoadingSkeleton rows={5} />;
  if (error) return <ErrorState message={error} onRetry={load} />;
  if (!data) return null;

  return (
    <div className="space-y-4">
      <DisclaimerBanner />
      <section className="rounded-[8px] bg-text p-5 text-white">
        <p className="text-sm font-semibold text-white/70">StoPro</p>
        <h1 className="mt-2 text-2xl font-black">이성현</h1>
        <p className="mt-2 text-sm leading-6 text-white/75">관심종목, 리스크 알림, 최근 분석을 실제 데이터 기준으로 점검합니다.</p>
        <div className="mt-4 grid grid-cols-3 gap-2">
          <Link href="/analyze" className="inline-flex min-h-11 items-center justify-center gap-1 rounded-[8px] bg-white text-xs font-black text-text">
            <Search className="h-4 w-4" />
            분석
          </Link>
          <Link href="/watchlist" className="inline-flex min-h-11 items-center justify-center gap-1 rounded-[8px] bg-white/10 text-xs font-black text-white">
            <Star className="h-4 w-4" />
            관심
          </Link>
          <Link href="/positions" className="inline-flex min-h-11 items-center justify-center gap-1 rounded-[8px] bg-white/10 text-xs font-black text-white">
            <BriefcaseBusiness className="h-4 w-4" />
            보유
          </Link>
        </div>
      </section>
      <TodaySummaryCard data={data} />
      {data.watchlistCount === 0 ? (
        <EmptyState title="관심종목이 없습니다" description="NVDA, TSLA, HIMS 같은 예시 종목을 추가해 바로 실제 데이터 분석을 시작할 수 있습니다.">
          {EXAMPLE_TICKERS.map((ticker) => (
            <Button key={ticker} variant="secondary" onClick={() => addExample(ticker)}>
              {ticker}
            </Button>
          ))}
        </EmptyState>
      ) : (
        <>
          <CandidateCard candidates={data.topCandidates} />
          <RiskAlertList riskAlerts={data.riskAlerts} triggeredAlerts={data.triggeredAlerts} />
          <WatchlistSignalTable signals={data.signals} />
        </>
      )}
      {data.recentlyAnalyzed.length > 0 && (
        <section className="rounded-[8px] border border-border bg-white p-5 shadow-soft">
          <div className="mb-4 flex items-center justify-between">
            <h2 className="font-bold text-text">최근 분석 종목</h2>
            <Link href="/analyze" className="flex items-center gap-1 text-xs font-bold text-primary">
              더 보기 <ArrowRight className="h-3 w-3" />
            </Link>
          </div>
          <div className="space-y-3">
            {data.recentlyAnalyzed.map((item) => (
              <Link key={`${item.ticker}-${item.createdAt}`} href={`/analyze?ticker=${item.ticker}`} className="block rounded-[8px] bg-cardSoft p-3">
                <p className="font-black text-text">{item.ticker} · {item.label}</p>
                <p className="mt-1 line-clamp-2 text-sm leading-6 text-subText">{item.summary}</p>
              </Link>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
