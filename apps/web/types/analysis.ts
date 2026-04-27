export type DecisionStatus = "candidate" | "split_buy" | "watch" | "caution" | "avoid";

export interface Decision {
  status: DecisionStatus;
  label: string;
  score: number;
  reason: string;
  buySuitabilityPercent?: number;
  buySuitability?: {
    percent: number;
    label: string;
    description: string;
    note: string;
    factors: { name: string; score: number; maxScore: number }[];
  };
}

export interface Indicators {
  rsi?: number | null;
  macd?: number | null;
  macdSignal?: number | null;
  stochasticK?: number | null;
  stochasticD?: number | null;
  ma20?: number | null;
  ma60?: number | null;
  ma200?: number | null;
  atr?: number | null;
  bollingerUpper?: number | null;
  bollingerLower?: number | null;
  volumeRatio?: number | null;
  adx?: number | null;
  plusDI?: number | null;
  minusDI?: number | null;
  mfi?: number | null;
  obvTrend?: number | null;
  support20?: number | null;
  resistance20?: number | null;
  support60?: number | null;
  resistance60?: number | null;
  distanceFrom52WeekHighPercent?: number | null;
}

export interface StrategyPlan {
  entryPrice?: number | null;
  firstBuyZone?: number | null;
  secondBuyZone?: number | null;
  firstTarget?: number | null;
  secondTarget?: number | null;
  stopLoss?: number | null;
  invalidationCondition: string;
  message?: string;
  plan: { step: string; condition: string; weight: number }[];
}

export interface AnalysisResponse {
  ticker: string;
  name: string;
  currency: string;
  exchangeRate: number;
  usdKrw?: number;
  currentPrice: number;
  previousClose?: number | null;
  dailyChange?: number | null;
  dailyChangePercent?: number | null;
  dataTimestamp?: string | null;
  isDelayed: boolean;
  cacheHit: boolean;
  decision: Decision;
  summary: string;
  quote: {
    price?: number | null;
    volume?: number | null;
    averageVolume?: number | null;
    fiftyTwoWeekHigh?: number | null;
    fiftyTwoWeekLow?: number | null;
  };
  indicators: Indicators;
  strategy: StrategyPlan;
  positionSizing: {
    capitalKRW: number;
    riskPercent: number;
    riskAmountKRW: number;
    riskPerShareKRW?: number | null;
    quantity: number;
    referenceQuantity?: number;
    estimatedCapitalKRW: number;
    remainingCashKRW: number;
    warning?: string | null;
  };
  profitLoss: {
    firstTargetProfitKRW: number;
    secondTargetProfitKRW: number;
    stopLossLossKRW: number;
    firstTargetReturnPercent: number;
    secondTargetReturnPercent: number;
    stopLossReturnPercent: number;
  };
  rewardRisk: {
    ratioToFirstTarget?: number | null;
    ratioToSecondTarget?: number | null;
    label: string;
    description: string;
  };
  risk: {
    score: number;
    label: string;
    description: string;
    factors: { name: string; score: number; description: string }[];
  };
  scenarios: {
    name: string;
    probability: number;
    condition: string;
    response: string;
    checkPrice?: number | null;
  }[];
  fundamentals: {
    marketCap?: number | null;
    trailingPE?: number | null;
    forwardPE?: number | null;
    eps?: number | null;
    profitMargin?: number | null;
    revenueGrowth?: number | null;
    debtToEquity?: number | null;
    dataAvailable: boolean;
    notes: string[];
  };
  backtest: {
    period: string;
    sampleCount: number;
    winRate: number;
    averageReturnPercent: number;
    maxLossPercent: number;
    averageHoldingDays: number;
    reliability: string;
    warning?: string | null;
  };
  dataQuality: {
    source: string;
    status: "good" | "partial" | "poor";
    hasEnoughHistory: boolean;
    missingRows: number;
    missingVolumeRows?: number;
    latestCloseExists: boolean;
    indicatorsAvailable: boolean;
    analysisAvailable: boolean;
    lastUpdated: string;
    cacheHit: boolean;
    isRealtime: boolean;
    message: string;
  };
  chart: ChartPoint[];
  disclaimer: string;
}

export interface ChartPoint {
  date: string;
  open?: number | null;
  high?: number | null;
  low?: number | null;
  close?: number | null;
  volume?: number | null;
  ma20?: number | null;
  ma60?: number | null;
  ma200?: number | null;
}

export interface DashboardResponse {
  watchlistCount: number;
  positionCount: number;
  candidateCount: number;
  cautionCount: number;
  triggeredAlertCount: number;
  signals: WatchlistSignal[];
  topCandidates: WatchlistSignal[];
  riskAlerts: WatchlistSignal[];
  triggeredAlerts: TriggeredAlert[];
  recentlyAnalyzed: {
    ticker: string;
    label: string;
    summary: string;
    riskScore: number;
    rewardRiskRatio?: number | null;
    createdAt: string;
    price?: number | null;
  }[];
  errors: { ticker: string; message: string }[];
}

export interface WatchlistSignal {
  ticker: string;
  name?: string;
  price?: number | null;
  dailyChangePercent?: number | null;
  decision: DecisionStatus;
  decisionLabel: string;
  riskScore?: number | null;
  rewardRiskRatio?: number | null;
  lastAnalyzedAt?: string | null;
  priceBelowMA20?: boolean;
  macdBullish?: boolean;
}

export interface TriggeredAlert {
  id: number;
  ticker: string;
  conditionType: string;
  targetPrice: number;
  message?: string | null;
  currentPrice?: number | null;
  triggered: boolean;
}

export interface SymbolSearchResult {
  name: string;
  ticker: string;
  market: string;
  exchange: string;
  currency: string;
}
