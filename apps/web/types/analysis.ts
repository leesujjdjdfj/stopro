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
  displayTicker?: string;
  name: string;
  market?: string | null;
  exchange?: string | null;
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
  supportResistance?: {
    support?: SupportResistanceLevel | null;
    resistance?: SupportResistanceLevel | null;
    atr?: number | null;
    tolerance?: number | null;
    method?: string;
    lookbackDays?: number;
  };
  investmentInsight?: InvestmentInsight;
  chart: ChartPoint[];
  disclaimer: string;
}

export interface InsightDetail {
  condition: string;
  passed: boolean;
  value: string;
  impact: string;
}

export interface InsightBreakdown {
  key: string;
  name: string;
  score: number;
  maxScore: number;
  label: string;
  summary: string;
  details?: InsightDetail[];
}

export interface InvestmentInsight {
  finalLabel: string;
  score: number;
  tone: "positive" | "cautious" | "neutral" | "warning" | "danger";
  oneLine: string;
  summary: string;
  technicalScore: number;
  newsScore: number;
  totalScore: number;
  confidence: "high" | "medium" | "low";
  scoreBreakdown: InsightBreakdown[];
  positivePoints: string[];
  negativePoints: string[];
  watchPoints: string[];
  riskManagement: {
    supportPrice?: number | null;
    resistancePrice?: number | null;
    stopLossGuide?: number | null;
    invalidationCondition: string;
    supportDistancePercent?: number | null;
    resistanceDistancePercent?: number | null;
  };
  newsInsight: {
    sentiment: NewsSentiment;
    sentimentScore: number;
    oneLine: string;
    keyIssues: string[];
    positiveFactors: string[];
    negativeFactors: string[];
    riskFactors: string[];
    watchPoints: string[];
    articlesUsed: number;
    confidence: "high" | "medium" | "low";
  };
  technicalVsNews: {
    alignment: "aligned" | "diverged" | "mixed" | "insufficient";
    label?: string;
    message?: string;
    summary: string;
    newsDirection?: "positive" | "negative" | "mixed" | "insufficient";
    chartDirection?: "bullish" | "weak" | "mixed" | "insufficient";
  };
  newsChartAlignment?: {
    alignment: "aligned" | "diverged" | "mixed" | "insufficient";
    label?: string;
    message?: string;
    summary: string;
    newsDirection?: "positive" | "negative" | "mixed" | "insufficient";
    chartDirection?: "bullish" | "weak" | "mixed" | "insufficient";
  };
  scenarios: {
    name: string;
    condition: string;
    interpretation: string;
    actionGuide: string;
  }[];
  disclaimer: string;
}

export interface SupportResistanceLevel {
  price: number;
  strength: "weak" | "normal" | "strong";
  touchCount: number;
  distancePercent: number;
  score?: number | null;
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
  displayTicker?: string;
  name?: string;
  market?: string | null;
  exchange?: string | null;
  currency?: string | null;
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

export interface NewsArticle {
  title: string;
  description?: string | null;
  url: string;
  source?: string | null;
  publishedAt?: string | null;
}

export type NewsSentiment = "positive" | "neutral" | "negative" | "mixed";

export interface NewsAnalysisResponse {
  ticker: string;
  companyName: string;
  newsSource: string;
  aiProvider: string;
  sentiment: NewsSentiment;
  sentimentScore: number;
  oneLine: string;
  summary: string;
  keyIssues: string[];
  positiveFactors: string[];
  negativeFactors: string[];
  riskFactors: string[];
  watchPoints: string[];
  technicalVsNews?: "aligned" | "diverged" | "mixed" | "insufficient";
  newsItems: NewsArticle[];
  confidence: "high" | "medium" | "low";
  cacheHit: boolean;
  disclaimer: string;
}
