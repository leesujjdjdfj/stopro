"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Search, Star, X } from "lucide-react";
import { Button } from "@/components/common/Button";
import { api } from "@/lib/api";
import type { SymbolSearchResult } from "@/types/analysis";

const RECENT_KEY = "stopro-recent-symbol-searches";
const FAVORITE_KEY = "stopro-favorite-symbol-searches";

export function StockSearchBox({
  ticker,
  onTickerChange,
  onSelect,
  onSubmit,
  loading
}: {
  ticker: string;
  onTickerChange: (value: string) => void;
  onSelect?: (result: SymbolSearchResult) => void;
  onSubmit: (tickerOverride?: string) => void;
  loading: boolean;
}) {
  const [query, setQuery] = useState(ticker);
  const [results, setResults] = useState<SymbolSearchResult[]>([]);
  const [recent, setRecent] = useState<SymbolSearchResult[]>([]);
  const [favorites, setFavorites] = useState<SymbolSearchResult[]>([]);
  const [isOpen, setIsOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(0);
  const [error, setError] = useState("");
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setQuery((current) => (current === ticker || !current ? ticker : current));
  }, [ticker]);

  useEffect(() => {
    setRecent(readStorage(RECENT_KEY));
    setFavorites(readStorage(FAVORITE_KEY));
  }, []);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (!boxRef.current?.contains(event.target as Node)) setIsOpen(false);
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 1) {
      setResults([]);
      setError("");
      return;
    }
    const timer = window.setTimeout(async () => {
      try {
        const rows = await api.searchSymbols(trimmed);
        setResults(rows.slice(0, 10));
        setActiveIndex(0);
        setError("");
        setIsOpen(true);
      } catch {
        const fallback = localFallbackSearch(trimmed);
        setResults(fallback);
        setError(fallback.length ? "" : "네트워크 오류로 검색 결과를 가져오지 못했습니다.");
        setActiveIndex(0);
        setIsOpen(true);
      }
    }, 300);
    return () => window.clearTimeout(timer);
  }, [query]);

  const visibleSuggestions = useMemo(() => {
    if (query.trim()) return results;
    const merged = [...favorites, ...recent];
    const seen = new Set<string>();
    return merged.filter((item) => {
      const key = `${item.ticker}:${item.name}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).slice(0, 10);
  }, [favorites, query, recent, results]);

  const choose = (result: SymbolSearchResult) => {
    setQuery(result.name);
    onTickerChange(result.ticker);
    onSelect?.(result);
    setIsOpen(false);
    const next = [result, ...recent.filter((item) => `${item.ticker}:${item.name}` !== `${result.ticker}:${result.name}`)].slice(0, 5);
    setRecent(next);
    writeStorage(RECENT_KEY, next);
    window.setTimeout(() => onSubmit(result.ticker), 0);
  };

  const submitCurrent = () => {
    const selected = visibleSuggestions[activeIndex];
    if (isOpen && selected && query.trim()) {
      choose(selected);
      return;
    }
    const value = ticker || query.trim().toUpperCase();
    onTickerChange(value);
    onSubmit(value);
    setIsOpen(false);
  };

  const toggleFavorite = (item: SymbolSearchResult) => {
    const key = `${item.ticker}:${item.name}`;
    const exists = favorites.some((favorite) => `${favorite.ticker}:${favorite.name}` === key);
    const next = exists ? favorites.filter((favorite) => `${favorite.ticker}:${favorite.name}` !== key) : [item, ...favorites].slice(0, 10);
    setFavorites(next);
    writeStorage(FAVORITE_KEY, next);
  };

  return (
    <div ref={boxRef} className="relative rounded-[8px] border border-border bg-white p-3 shadow-soft">
      <label className="mb-2 block text-xs font-bold text-subText">종목 검색</label>
      <div className="flex gap-2">
        <div className="flex min-w-0 flex-1 items-center gap-2 rounded-[8px] bg-cardSoft px-3">
          <Search className="h-4 w-4 shrink-0 text-subText" />
          <input
            value={query}
            onFocus={() => setIsOpen(true)}
            onChange={(event) => {
              const value = event.target.value;
              setQuery(value);
              if (looksLikeTicker(value)) onTickerChange(value.toUpperCase());
            }}
            onKeyDown={(event) => {
              if (event.key === "ArrowDown") {
                event.preventDefault();
                setActiveIndex((index) => Math.min(index + 1, Math.max(visibleSuggestions.length - 1, 0)));
              } else if (event.key === "ArrowUp") {
                event.preventDefault();
                setActiveIndex((index) => Math.max(index - 1, 0));
              } else if (event.key === "Enter") {
                event.preventDefault();
                submitCurrent();
              } else if (event.key === "Escape") {
                setIsOpen(false);
              }
            }}
            placeholder="종목 검색 (예: 삼성전자, NVDA, 테슬라)"
            className="min-h-11 w-full bg-transparent text-base font-black text-text outline-none placeholder:text-subText"
          />
          {query && (
            <button
              type="button"
              title="입력 지우기"
              onClick={() => {
                setQuery("");
                onTickerChange("");
                setResults([]);
                setIsOpen(true);
              }}
              className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full text-subText active:bg-border"
            >
              <X className="h-4 w-4" />
            </button>
          )}
        </div>
        <Button onClick={submitCurrent} disabled={!(ticker || query).trim() || loading} className="px-5">
          분석
        </Button>
      </div>
      {isOpen && (
        <div className="absolute left-3 right-3 top-[88px] z-30 overflow-hidden rounded-[8px] border border-border bg-white shadow-soft">
          {!query.trim() && favorites.length > 0 && <p className="px-4 pt-3 text-[11px] font-black text-subText">즐겨찾기 / 최근 검색</p>}
          {visibleSuggestions.length > 0 ? (
            <div className="max-h-[330px] overflow-y-auto py-2">
              {visibleSuggestions.map((item, index) => {
                const favorite = favorites.some((fav) => fav.ticker === item.ticker && fav.name === item.name);
                return (
                  <div
                    key={`${item.ticker}-${item.name}-${index}`}
                    className={`flex min-h-14 items-center gap-2 px-3 ${index === activeIndex ? "bg-primary/10" : "bg-white"}`}
                  >
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => toggleFavorite(item)} title="즐겨찾기" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-[8px] text-warning active:bg-warning/10">
                      <Star className={`h-4 w-4 ${favorite ? "fill-warning" : ""}`} />
                    </button>
                    <button type="button" onMouseDown={(event) => event.preventDefault()} onClick={() => choose(item)} className="min-w-0 flex-1 py-2 text-left">
                      <p className="truncate text-sm font-black text-text">[{item.name}] {item.ticker} • {item.market}</p>
                      <p className="mt-0.5 text-xs font-semibold text-subText">{item.exchange} · {item.currency}</p>
                    </button>
                  </div>
                );
              })}
            </div>
          ) : (
            <p className="px-4 py-5 text-sm font-semibold text-subText">{error || "검색 결과가 없습니다"}</p>
          )}
        </div>
      )}
    </div>
  );
}

function looksLikeTicker(value: string) {
  return /^[a-zA-Z0-9.\-]{1,12}$/.test(value.trim());
}

function readStorage(key: string): SymbolSearchResult[] {
  try {
    return JSON.parse(window.localStorage.getItem(key) || "[]").slice(0, 10);
  } catch {
    return [];
  }
}

function writeStorage(key: string, value: SymbolSearchResult[]) {
  window.localStorage.setItem(key, JSON.stringify(value));
}

const FALLBACK_SYMBOLS: SymbolSearchResult[] = [
  { name: "삼성전자", ticker: "005930", market: "KOSPI", exchange: "KRX", currency: "KRW" },
  { name: "SK하이닉스", ticker: "000660", market: "KOSPI", exchange: "KRX", currency: "KRW" },
  { name: "현대차", ticker: "005380", market: "KOSPI", exchange: "KRX", currency: "KRW" },
  { name: "한화에어로스페이스", ticker: "012450", market: "KOSPI", exchange: "KRX", currency: "KRW" },
  { name: "카카오", ticker: "035720", market: "KOSPI", exchange: "KRX", currency: "KRW" },
  { name: "네이버", ticker: "035420", market: "KOSPI", exchange: "KRX", currency: "KRW" },
  { name: "에코프로비엠", ticker: "247540", market: "KOSDAQ", exchange: "KRX", currency: "KRW" },
  { name: "알테오젠", ticker: "196170", market: "KOSDAQ", exchange: "KRX", currency: "KRW" },
  { name: "엔비디아", ticker: "NVDA", market: "NASDAQ", exchange: "NASDAQ", currency: "USD" },
  { name: "NVIDIA", ticker: "NVDA", market: "NASDAQ", exchange: "NASDAQ", currency: "USD" },
  { name: "테슬라", ticker: "TSLA", market: "NASDAQ", exchange: "NASDAQ", currency: "USD" },
  { name: "Tesla", ticker: "TSLA", market: "NASDAQ", exchange: "NASDAQ", currency: "USD" },
  { name: "Apple", ticker: "AAPL", market: "NASDAQ", exchange: "NASDAQ", currency: "USD" },
  { name: "Microsoft", ticker: "MSFT", market: "NASDAQ", exchange: "NASDAQ", currency: "USD" },
  { name: "Palantir", ticker: "PLTR", market: "NASDAQ", exchange: "NASDAQ", currency: "USD" }
];

function localFallbackSearch(query: string) {
  const q = query.toLowerCase();
  const matches = FALLBACK_SYMBOLS.filter((item) => item.name.toLowerCase().includes(q) || item.ticker.toLowerCase().includes(q));
  if (matches.length) return matches.slice(0, 10);
  const raw = query.trim().toUpperCase();
  if (/^\d{6}$/.test(raw)) return [{ name: `KRX ${raw}`, ticker: raw, market: "KRX", exchange: "KRX", currency: "KRW" }];
  if (/^[A-Z][A-Z0-9.\-]{0,7}$/.test(raw)) return [{ name: raw, ticker: raw, market: "US", exchange: "US", currency: "USD" }];
  return [];
}
