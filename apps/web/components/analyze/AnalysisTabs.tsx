"use client";

import { Plus } from "lucide-react";
import { AiSummaryCard } from "@/components/analyze/AiSummaryCard";
import { BacktestSummaryCard } from "@/components/analyze/BacktestSummaryCard";
import { DataQualityCard } from "@/components/analyze/DataQualityCard";
import { DecisionCard } from "@/components/analyze/DecisionCard";
import { FundamentalCheckCard } from "@/components/analyze/FundamentalCheckCard";
import { IndicatorGrid } from "@/components/analyze/IndicatorGrid";
import { MemoCard } from "@/components/analyze/MemoCard";
import { NewsAiAnalysisCard } from "@/components/analyze/NewsAiAnalysisCard";
import { QuoteCard } from "@/components/analyze/QuoteCard";
import { RewardRiskCard } from "@/components/analyze/RewardRiskCard";
import { RiskScoreCard } from "@/components/analyze/RiskScoreCard";
import { StockInfoPanel } from "@/components/analyze/StockInfoPanel";
import { StrategyPlanCard } from "@/components/analyze/StrategyPlanCard";
import { Button } from "@/components/common/Button";
import type { AnalysisResponse } from "@/types/analysis";
import { useRef, useState } from "react";

type TabKey = "ai" | "info" | "indicators" | "strategy";

const tabs: { key: TabKey; label: string }[] = [
  { key: "ai", label: "AI 분석" },
  { key: "info", label: "종목 정보" },
  { key: "indicators", label: "지표" },
  { key: "strategy", label: "내 전략" }
];

export function AnalysisTabs({ analysis, onAddToWatchlist }: { analysis: AnalysisResponse; onAddToWatchlist: () => void }) {
  const [activeTab, setActiveTab] = useState<TabKey>("ai");
  const contentRef = useRef<HTMLDivElement | null>(null);

  const selectTab = (tab: TabKey) => {
    setActiveTab(tab);
    window.requestAnimationFrame(() => {
      const target = contentRef.current;
      if (!target) return;
      const headerOffset = 128;
      const top = target.getBoundingClientRect().top + window.scrollY - headerOffset;
      window.scrollTo({ top: Math.max(0, top), behavior: "smooth" });
    });
  };

  return (
    <section className="space-y-4">
      <div className="sticky top-[73px] z-30 -mx-4 border-b border-border bg-white px-4 pt-1 shadow-[0_8px_20px_rgba(15,23,42,0.04)]">
        <div className="scrollbar-none flex gap-6 overflow-x-auto" role="tablist" aria-label="분석 카테고리">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              type="button"
              role="tab"
              aria-selected={activeTab === tab.key}
              onClick={() => selectTab(tab.key)}
              className={`relative h-12 shrink-0 text-sm font-black transition ${activeTab === tab.key ? "text-primary" : "text-subText"}`}
            >
              {tab.label}
              {activeTab === tab.key ? <span className="absolute bottom-0 left-0 h-0.5 w-full rounded-full bg-primary" /> : null}
            </button>
          ))}
        </div>
      </div>

      <div ref={contentRef} className="scroll-mt-32 space-y-4">
        {activeTab === "ai" ? (
          <>
            <AiSummaryCard analysis={analysis} />
            <DecisionCard analysis={analysis} />
            <div className="grid grid-cols-1 gap-4">
              <RewardRiskCard analysis={analysis} />
              <RiskScoreCard analysis={analysis} />
            </div>
            <NewsAiAnalysisCard analysis={analysis} />
            <BacktestSummaryCard analysis={analysis} />
            <Button variant="secondary" className="w-full" onClick={onAddToWatchlist}>
              <Plus className="h-4 w-4" />
              관심종목에 저장
            </Button>
          </>
        ) : null}

        {activeTab === "info" ? (
          <>
            <StockInfoPanel analysis={analysis} />
            <QuoteCard analysis={analysis} />
            <FundamentalCheckCard analysis={analysis} />
            <DataQualityCard analysis={analysis} />
          </>
        ) : null}

        {activeTab === "indicators" ? (
          <>
            <IndicatorGrid analysis={analysis} />
            <BacktestSummaryCard analysis={analysis} />
          </>
        ) : null}

        {activeTab === "strategy" ? (
          <>
            <StrategyPlanCard analysis={analysis} />
            <MemoCard ticker={analysis.ticker} />
          </>
        ) : null}
      </div>
    </section>
  );
}
