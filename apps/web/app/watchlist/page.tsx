"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { Button } from "@/components/common/Button";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { WatchlistForm } from "@/components/watchlist/WatchlistForm";
import { WatchlistTable } from "@/components/watchlist/WatchlistTable";
import { api } from "@/lib/api";
import { EXAMPLE_TICKERS } from "@/lib/constants";
import type { WatchlistItem } from "@/types/portfolio";

export default function WatchlistPage() {
  const [items, setItems] = useState<WatchlistItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setItems(await api.getWatchlist());
    } catch (err) {
      setError(err instanceof Error ? err.message : "관심종목을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const add = async (ticker: string, note?: string) => {
    setSaving(true);
    await api.addWatchlist({ ticker, note });
    setSaving(false);
    await load();
  };

  const analyzeAll = async () => {
    setSaving(true);
    try {
      await api.analyzeAllWatchlist();
      await load();
    } finally {
      setSaving(false);
    }
  };

  if (loading) return <LoadingSkeleton rows={4} />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="space-y-4">
      <WatchlistForm onAdd={add} loading={saving} />
      <Button className="w-full" variant="secondary" onClick={analyzeAll} disabled={saving || items.length === 0}>
        <RefreshCw className="h-4 w-4" />
        전체 재분석
      </Button>
      {items.length === 0 ? (
        <EmptyState title="관심종목이 없습니다" description="자주 확인할 종목을 저장하면 대시보드에서 우선순위와 위험 신호를 볼 수 있습니다.">
          {EXAMPLE_TICKERS.map((ticker) => (
            <Button key={ticker} variant="secondary" onClick={() => add(ticker, "예시 관심종목")}>
              {ticker}
            </Button>
          ))}
        </EmptyState>
      ) : (
        <WatchlistTable
          items={items}
          onDelete={async (ticker) => {
            await api.deleteWatchlist(ticker);
            await load();
          }}
        />
      )}
    </div>
  );
}
