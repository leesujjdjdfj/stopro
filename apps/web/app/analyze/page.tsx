"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { Plus } from "lucide-react";
import { AiSummaryCard } from "@/components/analyze/AiSummaryCard";
import { BacktestSummaryCard } from "@/components/analyze/BacktestSummaryCard";
import { CapitalInput } from "@/components/analyze/CapitalInput";
import { DataQualityCard } from "@/components/analyze/DataQualityCard";
import { DecisionCard } from "@/components/analyze/DecisionCard";
import { FundamentalCheckCard } from "@/components/analyze/FundamentalCheckCard";
import { IndicatorGrid } from "@/components/analyze/IndicatorGrid";
import { MemoCard } from "@/components/analyze/MemoCard";
import { PositionSizingCard } from "@/components/analyze/PositionSizingCard";
import { PriceChartCard } from "@/components/analyze/PriceChartCard";
import { ProfitLossSimulationCard } from "@/components/analyze/ProfitLossSimulationCard";
import { QuoteCard } from "@/components/analyze/QuoteCard";
import { RewardRiskCard } from "@/components/analyze/RewardRiskCard";
import { RiskScoreCard } from "@/components/analyze/RiskScoreCard";
import { ScenarioCard } from "@/components/analyze/ScenarioCard";
import { StockSearchBox } from "@/components/analyze/StockSearchBox";
import { StrategyPlanCard } from "@/components/analyze/StrategyPlanCard";
import { Button } from "@/components/common/Button";
import { DisclaimerBanner } from "@/components/common/DisclaimerBanner";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { api } from "@/lib/api";
import { useAnalysisStore } from "@/store/analysisStore";
import type { AnalysisResponse } from "@/types/analysis";

export default function AnalyzePage() {
  const store = useAnalysisStore();
  const [ticker, setTicker] = useState("NVDA");
  const [capital, setCapital] = useState(5_000_000);
  const [riskProfile, setRiskProfile] = useState("balanced");
  const [analysis, setAnalysis] = useState<AnalysisResponse | undefined>();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const autoRan = useRef(false);

  useEffect(() => {
    setTicker(store.lastTicker || "NVDA");
    setCapital(store.lastCapitalKRW || 5_000_000);
    setRiskProfile(store.lastRiskProfile || "balanced");
    if (store.lastAnalysis) setAnalysis(store.lastAnalysis);
    api.getSettings().then((settings) => {
      if (!store.lastCapitalKRW && settings.defaultCapitalKRW) setCapital(Number(settings.defaultCapitalKRW));
      if (!store.lastRiskProfile && settings.defaultRiskProfile) setRiskProfile(settings.defaultRiskProfile);
    }).catch(() => undefined);
  }, []);

  const runAnalyze = useCallback(
    async (targetTicker = ticker, targetCapital = capital, targetRisk = riskProfile) => {
      const normalized = targetTicker.trim().toUpperCase();
      if (!normalized) return;
      setLoading(true);
      setError("");
      store.setLastInput(normalized, targetCapital, targetRisk);
      try {
        const result = await api.analyze({ ticker: normalized, capitalKRW: targetCapital, riskProfile: targetRisk });
        setAnalysis(result);
        store.setLastAnalysis(result);
      } catch (err) {
        setError(err instanceof Error ? err.message : "분석에 실패했습니다.");
      } finally {
        setLoading(false);
      }
    },
    [capital, riskProfile, store, ticker]
  );

  useEffect(() => {
    if (autoRan.current) return;
    const param = new URLSearchParams(window.location.search).get("ticker");
    if (param) {
      autoRan.current = true;
      const normalized = param.toUpperCase();
      setTicker(normalized);
      void runAnalyze(normalized, capital, riskProfile);
    }
  }, [capital, riskProfile, runAnalyze]);

  const addToWatchlist = async () => {
    if (!analysis) return;
    await api.addWatchlist({ ticker: analysis.ticker, note: "분석 화면에서 추가" });
  };

  return (
    <div className="space-y-4">
      <DisclaimerBanner />
      <StockSearchBox ticker={ticker} onTickerChange={setTicker} onSubmit={(selectedTicker) => runAnalyze(selectedTicker)} loading={loading} />
      <CapitalInput capital={capital} riskProfile={riskProfile} onCapitalChange={setCapital} onRiskProfileChange={setRiskProfile} />
      {loading && <LoadingSkeleton rows={4} />}
      {error && <ErrorState message={error} onRetry={() => runAnalyze()} />}
      {analysis && !loading && (
        <>
          <AiSummaryCard analysis={analysis} />
          <div className="grid grid-cols-1 gap-4">
            <DecisionCard analysis={analysis} />
            <RewardRiskCard analysis={analysis} />
            <RiskScoreCard analysis={analysis} />
          </div>
          <Button variant="secondary" className="w-full" onClick={addToWatchlist}>
            <Plus className="h-4 w-4" />
            관심종목에 저장
          </Button>
          <QuoteCard analysis={analysis} />
          <StrategyPlanCard analysis={analysis} />
          <PositionSizingCard analysis={analysis} />
          <ProfitLossSimulationCard analysis={analysis} />
          <ScenarioCard analysis={analysis} />
          <IndicatorGrid analysis={analysis} />
          <FundamentalCheckCard analysis={analysis} />
          <BacktestSummaryCard analysis={analysis} />
          <PriceChartCard analysis={analysis} />
          <DataQualityCard analysis={analysis} />
          <MemoCard ticker={analysis.ticker} />
        </>
      )}
    </div>
  );
}
