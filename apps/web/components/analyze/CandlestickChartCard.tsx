"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { Heart } from "lucide-react";
import {
  CandlestickSeries,
  ColorType,
  CrosshairMode,
  HistogramSeries,
  LineStyle,
  createChart,
  type CandlestickData,
  type HistogramData,
  type Time
} from "lightweight-charts";
import { Card } from "@/components/common/Card";
import { formatNumber, formatPercent, formatPrice } from "@/lib/format";
import type { AnalysisResponse, ChartPoint, SupportResistanceLevel } from "@/types/analysis";

const periods = [
  { label: "3M", days: 90 },
  { label: "6M", days: 140 },
  { label: "1Y", days: 260 },
  { label: "2Y", days: 520 }
] as const;

interface TooltipState {
  visible: boolean;
  left: number;
  top: number;
  date: string;
  open?: number;
  high?: number;
  low?: number;
  close?: number;
}

export function CandlestickChartCard({
  analysis,
  onAddToWatchlist
}: {
  analysis: AnalysisResponse;
  onAddToWatchlist?: () => void | Promise<void>;
}) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [period, setPeriod] = useState<(typeof periods)[number]>(periods[1]);
  const [tooltip, setTooltip] = useState<TooltipState>({ visible: false, left: 12, top: 12, date: "" });
  const [saved, setSaved] = useState(false);

  const visibleChart = useMemo(() => analysis.chart.slice(-period.days), [analysis.chart, period.days]);
  const support = analysis.supportResistance?.support ?? null;
  const resistance = analysis.supportResistance?.resistance ?? null;
  const chartData = useMemo(() => toChartSeries(visibleChart), [visibleChart]);
  const changeValue = analysis.dailyChange ?? null;
  const changePercent = analysis.dailyChangePercent ?? null;
  const changeTone = getChangeTone(changeValue ?? changePercent);
  const identity = getChartIdentity(analysis);

  useEffect(() => {
    const container = containerRef.current;
    if (!container || chartData.candles.length === 0) return;

    const chart = createChart(container, {
      autoSize: true,
      height: 350,
      layout: {
        background: { type: ColorType.Solid, color: "#FFFFFF" },
        textColor: "#6B7280",
        fontFamily: "Inter, ui-sans-serif, system-ui, sans-serif"
      },
      grid: {
        vertLines: { color: "#F3F4F6" },
        horzLines: { color: "#F3F4F6" }
      },
      rightPriceScale: {
        borderVisible: false,
        scaleMargins: { top: 0.08, bottom: 0.28 }
      },
      timeScale: {
        borderVisible: false,
        timeVisible: false,
        rightOffset: 6,
        barSpacing: window.innerWidth < 430 ? 7 : 8
      },
      crosshair: {
        mode: CrosshairMode.Normal,
        vertLine: { color: "#9CA3AF", labelBackgroundColor: "#111827" },
        horzLine: { color: "#9CA3AF", labelBackgroundColor: "#111827" }
      },
      localization: {
        priceFormatter: (price: number) => formatAxisPrice(price, analysis.currency)
      },
      handleScroll: {
        mouseWheel: true,
        pressedMouseMove: true,
        horzTouchDrag: true,
        vertTouchDrag: false
      },
      handleScale: {
        axisPressedMouseMove: true,
        mouseWheel: true,
        pinch: true
      }
    });

    const candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: "#EF4444",
      downColor: "#2563EB",
      borderUpColor: "#EF4444",
      borderDownColor: "#2563EB",
      wickUpColor: "#EF4444",
      wickDownColor: "#2563EB"
    });

    candleSeries.setData(chartData.candles);
    candleSeries.createPriceLine({
      price: analysis.currentPrice,
      color: "#111827",
      lineWidth: 1,
      lineStyle: LineStyle.Dashed,
      axisLabelVisible: true,
      title: "현재가"
    });

    if (resistance) {
      candleSeries.createPriceLine({
        price: resistance.price,
        color: "#EF4444",
        lineWidth: 1,
        lineStyle: LineStyle.Solid,
        axisLabelVisible: true,
        title: "저항"
      });
    }

    if (support) {
      candleSeries.createPriceLine({
        price: support.price,
        color: "#2563EB",
        lineWidth: 1,
        lineStyle: LineStyle.Solid,
        axisLabelVisible: true,
        title: "지지"
      });
    }

    const volumeSeries = chart.addSeries(HistogramSeries, {
      priceFormat: { type: "volume" },
      priceScaleId: "",
      color: "#E5E7EB"
    });
    volumeSeries.priceScale().applyOptions({ scaleMargins: { top: 0.78, bottom: 0 } });
    volumeSeries.setData(chartData.volumes);

    chart.timeScale().fitContent();

    chart.subscribeCrosshairMove((param) => {
      if (!param.point || !param.time || param.point.x < 0 || param.point.y < 0) {
        setTooltip((prev) => ({ ...prev, visible: false }));
        return;
      }
      const item = param.seriesData.get(candleSeries) as CandlestickData<Time> | undefined;
      if (!item) {
        setTooltip((prev) => ({ ...prev, visible: false }));
        return;
      }

      const width = container.clientWidth;
      setTooltip({
        visible: true,
        left: Math.min(param.point.x + 14, Math.max(12, width - 156)),
        top: Math.max(12, param.point.y - 82),
        date: String(param.time),
        open: item.open,
        high: item.high,
        low: item.low,
        close: item.close
      });
    });

    return () => {
      chart.remove();
    };
  }, [analysis.currency, analysis.currentPrice, chartData.candles, chartData.volumes, resistance, support]);

  const addToWatchlist = async () => {
    if (!onAddToWatchlist) return;
    await onAddToWatchlist();
    setSaved(true);
  };

  return (
    <Card>
      <div className="mb-4">
        <div className="flex items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="truncate text-xl font-black leading-7 text-text">
              {identity.name}
              {identity.code ? <span className="ml-2 text-base font-extrabold text-subText">{identity.code}</span> : null}
            </p>
            <p className="mt-3 text-[34px] font-black leading-none tracking-normal">
              <span className={changeTone}>{formatMainPrice(analysis.currentPrice, analysis.currency)}</span>
            </p>
            <p className={`mt-2 text-sm font-black ${changeTone}`}>
              {formatChangeLine(changeValue, changePercent, analysis.currency)}
            </p>
          </div>
          <button
            type="button"
            onClick={addToWatchlist}
            disabled={!onAddToWatchlist}
            aria-label="관심종목에 저장"
            className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-full border transition ${
              saved ? "border-warning/30 bg-warning/10 text-warning" : "border-border bg-white text-subText active:bg-cardSoft"
            } disabled:opacity-50`}
          >
            <Heart className="h-5 w-5" fill={saved ? "currentColor" : "none"} />
          </button>
        </div>
        <div className="mt-4 flex rounded-[8px] bg-cardSoft p-1">
          {periods.map((item) => (
            <button
              key={item.label}
              type="button"
              onClick={() => setPeriod(item)}
              className={`h-8 flex-1 rounded-[6px] px-2 text-[11px] font-black transition ${period.label === item.label ? "bg-white text-primary shadow-sm" : "text-subText"}`}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>
      <div className="mb-3 flex flex-wrap gap-2">
        {resistance ? <LevelChip tone="red" label="저항" value={formatPrice(resistance.price, analysis.currency)} meta={strengthLabel(resistance.strength, resistance.touchCount)} /> : null}
        {support ? <LevelChip tone="blue" label="지지" value={formatPrice(support.price, analysis.currency)} meta={strengthLabel(support.strength, support.touchCount)} /> : null}
        <LevelChip tone="dark" label="현재가" value={formatPrice(analysis.currentPrice, analysis.currency)} />
      </div>

      {chartData.candles.length ? (
        <div className="relative h-[350px] w-full overflow-hidden rounded-[8px] border border-border bg-white">
          <div ref={containerRef} className="h-full w-full touch-pan-x" />
          {tooltip.visible ? (
            <div
              className="pointer-events-none absolute z-10 w-36 rounded-[8px] border border-border bg-white/95 p-2 text-[11px] shadow-soft backdrop-blur"
              style={{ left: tooltip.left, top: tooltip.top }}
            >
              <p className="font-black text-text">{tooltip.date}</p>
              <TooltipRow label="시" value={tooltip.open} currency={analysis.currency} />
              <TooltipRow label="고" value={tooltip.high} currency={analysis.currency} tone="text-up" />
              <TooltipRow label="저" value={tooltip.low} currency={analysis.currency} tone="text-down" />
              <TooltipRow label="종" value={tooltip.close} currency={analysis.currency} />
            </div>
          ) : null}
        </div>
      ) : (
        <div className="flex h-[300px] items-center justify-center rounded-[8px] border border-dashed border-border bg-cardSoft p-6 text-center text-sm font-bold leading-6 text-subText">
          차트 데이터가 부족해 캔들 차트를 표시할 수 없습니다.
        </div>
      )}
      <p className="mt-3 text-xs leading-5 text-subText">
        거래량, 최근성, 가격 밀집도를 반영해 지지선과 저항선을 한 개씩 계산했습니다.
      </p>
      <SupportResistanceSummary support={support} resistance={resistance} />
    </Card>
  );
}

function getChartIdentity(analysis: AnalysisResponse) {
  const code = analysis.displayTicker || analysis.ticker || "";
  const rawName = analysis.name?.trim();
  const name = rawName && rawName.toUpperCase() !== code.toUpperCase() ? rawName : code || "종목명 확인 중";
  return { name, code: rawName && rawName.toUpperCase() !== code.toUpperCase() ? code : "" };
}

function getChangeTone(value?: number | null) {
  if (!value) return "text-subText";
  return value > 0 ? "text-up" : "text-down";
}

function formatMainPrice(value?: number | null, currency = "USD") {
  if (value === null || value === undefined || Number.isNaN(value)) return "시세 없음";
  if (currency === "KRW") return `${formatNumber(value, 0)}원`;
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2
  }).format(value);
}

function formatChangeLine(change?: number | null, percent?: number | null, currency = "USD") {
  if (change === null || change === undefined || Number.isNaN(change)) {
    return percent === null || percent === undefined || Number.isNaN(percent) ? "-" : `(${formatPercent(percent)})`;
  }
  const sign = change > 0 ? "+" : "";
  const changeText = currency === "KRW" ? `${sign}${formatNumber(change, 0)}원` : `${sign}${formatNumber(change, 2)}`;
  const percentText = percent === null || percent === undefined || Number.isNaN(percent) ? "-" : formatPercent(percent);
  return `${changeText} (${percentText})`;
}

function LevelChip({ tone, label, value, meta }: { tone: "red" | "blue" | "dark"; label: string; value: string; meta?: string }) {
  const classes = {
    red: "border-red-100 bg-red-50 text-up",
    blue: "border-blue-100 bg-blue-50 text-down",
    dark: "border-gray-200 bg-cardSoft text-text"
  };

  return (
    <span className={`rounded-full border px-3 py-1 text-[11px] font-black ${classes[tone]}`}>
      {label} {value}
      {meta ? <span className="ml-1 font-bold opacity-70">{meta}</span> : null}
    </span>
  );
}

function SupportResistanceSummary({
  support,
  resistance
}: {
  support?: SupportResistanceLevel | null;
  resistance?: SupportResistanceLevel | null;
}) {
  const supportDistance = support?.distancePercent;
  const resistanceDistance = resistance?.distancePercent;
  const supportNear = supportDistance !== undefined && Math.abs(supportDistance) < 3;
  const resistanceNear = resistanceDistance !== undefined && Math.abs(resistanceDistance) < 3;

  return (
    <div className="mt-3 grid grid-cols-2 gap-2">
      <DistanceBox
        label="지지까지 거리"
        value={supportDistance == null ? "-" : formatPercent(supportDistance)}
        note={supportNear ? "지지 근접 (매수 관점)" : "지지 확인"}
        tone="blue"
      />
      <DistanceBox
        label="저항까지 거리"
        value={resistanceDistance == null ? "-" : formatPercent(resistanceDistance)}
        note={resistanceNear ? "저항 근접 (관망)" : "저항 여유"}
        tone="red"
      />
    </div>
  );
}

function DistanceBox({ label, value, note, tone }: { label: string; value: string; note: string; tone: "blue" | "red" }) {
  return (
    <div className={`rounded-[8px] p-3 ${tone === "blue" ? "bg-blue-50 text-down" : "bg-red-50 text-up"}`}>
      <p className="text-[11px] font-bold opacity-70">{label}</p>
      <p className="mt-1 text-base font-black">{value}</p>
      <p className="mt-1 text-[11px] font-bold text-subText">{note}</p>
    </div>
  );
}

function strengthLabel(strength: "weak" | "normal" | "strong", touchCount: number) {
  const label = strength === "strong" ? "강함" : strength === "normal" ? "보통" : "약함";
  return `${label} · ${touchCount}회`;
}

function TooltipRow({ label, value, currency, tone = "text-text" }: { label: string; value?: number; currency: string; tone?: string }) {
  return (
    <div className="mt-1 flex items-center justify-between gap-2">
      <span className="font-bold text-subText">{label}</span>
      <span className={`font-black ${tone}`}>{formatPrice(value, currency)}</span>
    </div>
  );
}

function toChartSeries(points: ChartPoint[]): { candles: CandlestickData<Time>[]; volumes: HistogramData<Time>[] } {
  const candles: CandlestickData<Time>[] = [];
  const volumes: HistogramData<Time>[] = [];

  points.forEach((point) => {
    if (!isFiniteNumber(point.open) || !isFiniteNumber(point.high) || !isFiniteNumber(point.low) || !isFiniteNumber(point.close)) {
      return;
    }

    candles.push({
      time: point.date,
      open: point.open,
      high: point.high,
      low: point.low,
      close: point.close
    });
    volumes.push({
      time: point.date,
      value: point.volume ?? 0,
      color: point.close >= point.open ? "rgba(239, 68, 68, 0.28)" : "rgba(37, 99, 235, 0.28)"
    });
  });

  return { candles, volumes };
}

function formatAxisPrice(price: number, currency: string) {
  if (currency === "KRW") return formatNumber(price, 0);
  return price >= 1000 ? formatNumber(price, 0) : formatNumber(price, 2);
}

function isFiniteNumber(value?: number | null): value is number {
  return typeof value === "number" && Number.isFinite(value);
}
