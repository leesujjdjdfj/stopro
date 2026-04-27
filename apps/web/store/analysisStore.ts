"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { AnalysisResponse } from "@/types/analysis";

interface AnalysisState {
  lastTicker: string;
  lastAnalysis?: AnalysisResponse;
  setLastInput: (ticker: string) => void;
  setLastAnalysis: (analysis: AnalysisResponse) => void;
}

export const useAnalysisStore = create<AnalysisState>()(
  persist(
    (set) => ({
      lastTicker: "NVDA",
      setLastInput: (lastTicker) =>
        set({ lastTicker }),
      setLastAnalysis: (lastAnalysis) =>
        set({
          lastAnalysis,
          lastTicker: lastAnalysis.ticker
        })
    }),
    { name: "stopro-analysis" }
  )
);
