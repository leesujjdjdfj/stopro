import type { AnalysisResponse, DashboardResponse, SymbolSearchResult, TriggeredAlert } from "@/types/analysis";
import type { AlertItem, MemoItem, PositionItem, WatchlistItem } from "@/types/portfolio";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function apiFetch<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(options?.headers ?? {})
    },
    cache: "no-store"
  });
  if (!response.ok) {
    let message = "요청을 처리하지 못했습니다.";
    try {
      const body = await response.json();
      message = body.detail ?? message;
    } catch {
      message = response.statusText || message;
    }
    throw new Error(message);
  }
  return response.json() as Promise<T>;
}

export const api = {
  health: () => apiFetch<{ status: string }>("/health"),
  searchSymbols: (query: string) => apiFetch<SymbolSearchResult[]>(`/api/search?q=${encodeURIComponent(query)}&limit=10`),
  dashboard: () => apiFetch<DashboardResponse>("/api/dashboard"),
  analyze: (payload: { ticker: string; capitalKRW: number; riskProfile: string }) =>
    apiFetch<AnalysisResponse>("/api/analyze", { method: "POST", body: JSON.stringify(payload) }),
  getWatchlist: () => apiFetch<WatchlistItem[]>("/api/watchlist"),
  addWatchlist: (payload: { ticker: string; note?: string }) =>
    apiFetch<WatchlistItem>("/api/watchlist", { method: "POST", body: JSON.stringify(payload) }),
  deleteWatchlist: (ticker: string) => apiFetch<{ ok: boolean }>(`/api/watchlist/${ticker}`, { method: "DELETE" }),
  analyzeAllWatchlist: () => apiFetch<{ results: AnalysisResponse[]; errors: { ticker: string; message: string }[] }>("/api/watchlist/analyze-all", { method: "POST" }),
  getPositions: () => apiFetch<PositionItem[]>("/api/positions"),
  addPosition: (payload: { ticker: string; averagePrice: number; quantity: number; targetPrice?: number; stopLoss?: number; note?: string }) =>
    apiFetch<PositionItem>("/api/positions", { method: "POST", body: JSON.stringify(payload) }),
  updatePosition: (id: number, payload: { ticker: string; averagePrice: number; quantity: number; targetPrice?: number; stopLoss?: number; note?: string }) =>
    apiFetch<PositionItem>(`/api/positions/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deletePosition: (id: number) => apiFetch<{ ok: boolean }>(`/api/positions/${id}`, { method: "DELETE" }),
  getAlerts: () => apiFetch<AlertItem[]>("/api/alerts"),
  addAlert: (payload: { ticker: string; conditionType: string; targetPrice: number; message?: string; isActive: boolean }) =>
    apiFetch<AlertItem>("/api/alerts", { method: "POST", body: JSON.stringify(payload) }),
  updateAlert: (id: number, payload: { ticker: string; conditionType: string; targetPrice: number; message?: string; isActive: boolean }) =>
    apiFetch<AlertItem>(`/api/alerts/${id}`, { method: "PUT", body: JSON.stringify(payload) }),
  deleteAlert: (id: number) => apiFetch<{ ok: boolean }>(`/api/alerts/${id}`, { method: "DELETE" }),
  getTriggeredAlerts: () => apiFetch<TriggeredAlert[]>("/api/alerts/triggered"),
  getMemo: (ticker: string) => apiFetch<MemoItem>(`/api/memos/${ticker}`),
  saveMemo: (payload: { ticker: string; title?: string; thesis?: string; entryCondition?: string; stopCondition?: string; checklist?: string; review?: string }) =>
    apiFetch<MemoItem>("/api/memos", { method: "POST", body: JSON.stringify(payload) }),
  getSettings: () => apiFetch<Record<string, string>>("/api/settings"),
  updateSettings: (payload: Record<string, string>) => apiFetch<Record<string, string>>("/api/settings", { method: "PUT", body: JSON.stringify(payload) }),
  clearCache: () => apiFetch<{ ok: boolean }>("/api/settings/clear-cache", { method: "POST" }),
  resetDb: () => apiFetch<{ ok: boolean }>("/api/settings/reset-db", { method: "POST" })
};
