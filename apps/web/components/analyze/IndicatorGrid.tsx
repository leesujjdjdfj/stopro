import { Card } from "@/components/common/Card";
import { formatNumber, formatPrice } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function IndicatorGrid({ analysis }: { analysis: AnalysisResponse }) {
  const i = analysis.indicators;
  const ma5 = calculateMovingAverage(analysis.chart, 5);
  const items = [
    { label: "RSI", value: formatNumber(i.rsi, 1), note: rsiNote(i.rsi) },
    { label: "MACD", value: formatNumber(i.macd, 3), note: i.macd && i.macdSignal && i.macd > i.macdSignal ? "강세 전환" : "확인 필요" },
    { label: "Stochastic", value: `${formatNumber(i.stochasticK, 1)} / ${formatNumber(i.stochasticD, 1)}`, note: (i.stochasticK ?? 0) > 85 ? "과열권" : "보통" },
    { label: "MA5", value: formatPrice(ma5, analysis.currency), note: ma5 == null ? "부족" : analysis.currentPrice > ma5 ? "단기선 위" : "단기선 아래" },
    { label: "MA20", value: formatPrice(i.ma20, analysis.currency), note: analysis.currentPrice > (i.ma20 ?? Infinity) ? "위에 있음" : "아래에 있음" },
    { label: "MA60", value: formatPrice(i.ma60, analysis.currency), note: analysis.currentPrice > (i.ma60 ?? Infinity) ? "위에 있음" : "확인 필요" },
    { label: "MA200", value: formatPrice(i.ma200, analysis.currency), note: analysis.currentPrice > (i.ma200 ?? Infinity) ? "장기 추세 위" : "장기 추세 아래" },
    { label: "ATR", value: formatPrice(i.atr, analysis.currency), note: "변동성 기준" },
    { label: "Bollinger", value: `${formatPrice(i.bollingerLower, analysis.currency)} ~ ${formatPrice(i.bollingerUpper, analysis.currency)}`, note: "밴드 범위" },
    { label: "Volume Ratio", value: `${formatNumber(i.volumeRatio, 2)}배`, note: (i.volumeRatio ?? 0) > 1.5 ? "거래량 증가" : "평균권" },
    { label: "ADX", value: formatNumber(i.adx, 1), note: adxNote(i.adx, i.plusDI, i.minusDI) },
    { label: "MFI", value: formatNumber(i.mfi, 1), note: mfiNote(i.mfi) },
    { label: "OBV", value: `${formatNumber(i.obvTrend, 1)}일`, note: (i.obvTrend ?? 0) > 0 ? "누적 수급 개선" : "수급 확인 필요" },
    { label: "지지/저항", value: `${formatPrice(i.support20, analysis.currency)} / ${formatPrice(i.resistance20, analysis.currency)}`, note: "20일 기준" }
  ];
  return (
    <Card title="기술 지표">
      <div className="grid grid-cols-2 gap-3">
        {items.map((item) => (
          <div key={item.label} className="rounded-[8px] bg-cardSoft p-3">
            <p className="text-[11px] font-bold text-subText">{item.label}</p>
            <p className="mt-1 break-words text-sm font-black text-text">{item.value}</p>
            <p className="mt-1 text-[11px] font-semibold text-subText">{item.note}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}

function calculateMovingAverage(chart: AnalysisResponse["chart"], days: number) {
  const closes = chart
    .map((point) => point.close)
    .filter((value): value is number => typeof value === "number" && Number.isFinite(value))
    .slice(-days);
  if (closes.length < days) return null;
  return closes.reduce((sum, value) => sum + value, 0) / closes.length;
}

function rsiNote(value?: number | null) {
  if (value === null || value === undefined) return "부족";
  if (value > 70) return "과열 주의";
  if (value >= 40 && value <= 65) return "양호 범위";
  if (value < 35) return "약세/반등 확인";
  return "중립";
}

function adxNote(adx?: number | null, plusDI?: number | null, minusDI?: number | null) {
  if (adx === null || adx === undefined) return "부족";
  if (adx < 18) return "추세 약함";
  if ((plusDI ?? 0) > (minusDI ?? 0)) return "상승 추세 우위";
  return "하락 압력 우위";
}

function mfiNote(value?: number | null) {
  if (value === null || value === undefined) return "부족";
  if (value > 80) return "자금 흐름 과열";
  if (value < 20) return "침체/반등 확인";
  if (value >= 35 && value <= 75) return "보통권";
  return "확인 필요";
}
