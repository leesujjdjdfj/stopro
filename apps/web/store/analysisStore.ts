"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AnalysisResponse } from "@/types/analysis";

interface AnalysisState {
  lastTicker: string;
  lastCapitalKRW: number;
  lastRiskProfile: string;
  lastAnalysis?: AnalysisResponse;
  setLastInput: (ticker: string, capital: number, riskProfile: string) => void;
  setLastAnalysis: (analysis: AnalysisResponse) => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set) => ({
      lastTicker: "NVDA",
      lastCapitalKRW: 5_000_000,
      lastRiskProfile: "balanced",
      setLastInput: (lastTicker, lastCapitalKRW, lastRiskProfile) =>
        set({ lastTicker, lastCapitalKRW, lastRiskProfile }),
      setLastAnalysis: (lastAnalysis) =>
        set({
          lastAnalysis,
          lastTicker: lastAnalysis.ticker
        })
    }),
    { name: "stopro-analysis" }
  )
);
