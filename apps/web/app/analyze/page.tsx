"use client";

import dynamic from "next/dynamic";
import { useCallback, useEffect, useRef, useState } from "react";
import { AnalysisTabs } from "@/components/analyze/AnalysisTabs";
import { StockSearchBox } from "@/components/analyze/StockSearchBox";
import { DisclaimerBanner } from "@/components/common/DisclaimerBanner";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { api } from "@/lib/api";
import { useAnalysisStore } from "@/store/analysisStore";
import type { AnalysisResponse } from "@/types/analysis";

const CandlestickChartCard = dynamic(
  () => import("@/components/analyze/CandlestickChartCard").then((mod) => mod.CandlestickChartCard),
  {
    ssr: false,
    loading: () => <LoadingSkeleton rows={3} />
  }
);

export default function AnalyzePage() {
  const store = useAnalysisStore();
  const [ticker, setTicker] = useState("NVDA");
  const [analysis, setAnalysis] = useState<AnalysisResponse | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const autoRan = useRef(false);

  useEffect(() => {
    setTicker(store.lastTicker || "NVDA");
    if (store.lastAnalysis) setAnalysis(store.lastAnalysis);
  }, []);

  const runAnalyze = useCallback(
    async (targetTicker = ticker) => {
      const normalized = targetTicker.trim().toUpperCase();
      if (!normalized) return;
      setLoading(true);
      setError("");
      store.setLastInput(normalized);
      try {
        const result = await api.analyze({ ticker: normalized });
        setAnalysis(result);
        store.setLastAnalysis(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "분석에 실패했습니다.");
      } finally {
        setLoading(false);
      }
    },
    [store, ticker]
  );

  useEffect(() => {
    if (autoRan.current) return;
    const param = new URLSearchParams(window.location.search).get("ticker");
    if (param) {
      autoRan.current = true;
      const normalized = param.toUpperCase();
      setTicker(normalized);
      void runAnalyze(normalized);
    }
  }, [runAnalyze]);

  const addToWatchlist = async () => {
    if (!analysis) return;
    await api.addWatchlist({ ticker: analysis.ticker, note: "분석 화면에서 추가" });
  };

  return (
    <div className="space-y-4">
      <DisclaimerBanner />
      <StockSearchBox ticker={ticker} onTickerChange={setTicker} onSubmit={(selectedTicker) => runAnalyze(selectedTicker)} loading={loading} />
      {loading && <LoadingSkeleton rows={4} />}
      {error && <ErrorState message={error} onRetry={() => runAnalyze()} />}
      {analysis && !loading && (
        <div className="space-y-4">
          <CandlestickChartCard analysis={analysis} onAddToWatchlist={addToWatchlist} />
          <AnalysisTabs analysis={analysis} onAddToWatchlist={addToWatchlist} />
        </div>
      )}
    </div>
  );
}
