export interface WatchlistItem {
  id: number;
  ticker: string;
  note?: string | null;
  created_at: string;
  last_analyzed_at?: string | null;
  last_decision?: string | null;
  last_risk_score?: number | null;
  last_reward_risk_ratio?: number | null;
}

export interface PositionItem {
  id: number;
  ticker: string;
  average_price: number;
  quantity: number;
  target_price?: number | null;
  stop_loss?: number | null;
  note?: string | null;
  created_at: string;
  updated_at: string;
  currentPrice?: number | null;
  currentValue?: number | null;
  profitLoss?: number | null;
  profitLossPercent?: number | null;
  stopDistancePercent?: number | null;
  targetDistancePercent?: number | null;
  riskState?: string;
  riskReasons?: string[];
}

export interface AlertItem {
  id: number;
  ticker: string;
  condition_type: string;
  target_price: number;
  message?: string | null;
  is_active: boolean;
  triggered_at?: string | null;
  created_at: string;
}

export interface MemoItem {
  id?: number;
  ticker: string;
  title?: string | null;
  thesis?: string | null;
  entry_condition?: string | null;
  stop_condition?: string | null;
  checklist?: string | null;
  review?: string | null;
}
