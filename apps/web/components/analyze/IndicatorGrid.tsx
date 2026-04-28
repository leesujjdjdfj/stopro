"use client";

import { Info, X } from "lucide-react";
import { useEffect, useState } from "react";
import { Card } from "@/components/common/Card";
import { formatNumber, formatPrice } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

type IndicatorKey =
  | "RSI"
  | "MACD"
  | "Stochastic"
  | "MA5"
  | "MA20"
  | "MA60"
  | "MA200"
  | "ATR"
  | "Bollinger"
  | "Volume"
  | "ADX"
  | "MFI"
  | "OBV"
  | "SupportResistance";

interface IndicatorItem {
  key: IndicatorKey;
  label: string;
  value: string;
  note: string;
}

interface IndicatorContext {
  analysis: AnalysisResponse;
  item: IndicatorItem;
  ma5?: number | null;
}

const indicatorInfo: Record<
  IndicatorKey,
  {
    title: string;
    description: string;
    interpretation: (context: IndicatorContext) => string;
    viewpoints: string[];
  }
> = {
  RSI: {
    title: "RSI (상대강도지수)",
    description: "가격의 과매수/과매도 상태를 측정하는 지표",
    interpretation: ({ analysis }) => {
      const value = analysis.indicators.rsi;
      if (value == null) return "현재 RSI 데이터가 부족해 해석이 제한됩니다.";
      if (value > 70) return `현재 RSI ${formatNumber(value, 1)} → 과매수 구간, 추격 매수 주의`;
      if (value < 30) return `현재 RSI ${formatNumber(value, 1)} → 과매도 구간, 반등 가능성 확인`;
      if (value >= 65) return `현재 RSI ${formatNumber(value, 1)} → 과열 직전 구간`;
      return `현재 RSI ${formatNumber(value, 1)} → 중립 구간, 방향성 확인 필요`;
    },
    viewpoints: ["70 이상: 과매수 → 추격 매수 주의", "30 이하: 과매도 → 반등 가능성", "40~65: 비교적 안정적인 모멘텀 구간"]
  },
  MACD: {
    title: "MACD",
    description: "추세 전환과 모멘텀을 보는 지표",
    interpretation: ({ analysis }) => {
      const { macd, macdSignal } = analysis.indicators;
      if (macd == null || macdSignal == null) return "MACD 데이터가 부족해 해석이 제한됩니다.";
      return macd > macdSignal
        ? `MACD ${formatNumber(macd, 3)} > Signal ${formatNumber(macdSignal, 3)} → 상승 모멘텀`
        : `MACD ${formatNumber(macd, 3)} ≤ Signal ${formatNumber(macdSignal, 3)} → 모멘텀 확인 필요`;
    },
    viewpoints: ["MACD가 Signal 위: 상승 모멘텀 우위", "MACD가 Signal 아래: 약세 또는 조정 가능성", "교차 직후에는 거래량과 가격 확인이 중요"]
  },
  Stochastic: {
    title: "스토캐스틱",
    description: "단기 과열/침체를 판단하는 지표",
    interpretation: ({ analysis }) => {
      const { stochasticK, stochasticD } = analysis.indicators;
      if (stochasticK == null || stochasticD == null) return "스토캐스틱 데이터가 부족합니다.";
      if (stochasticK > 80) return `K ${formatNumber(stochasticK, 1)} / D ${formatNumber(stochasticD, 1)} → 과열 구간`;
      if (stochasticK < 20) return `K ${formatNumber(stochasticK, 1)} / D ${formatNumber(stochasticD, 1)} → 과매도 구간`;
      return `K ${formatNumber(stochasticK, 1)} / D ${formatNumber(stochasticD, 1)} → 보통 구간`;
    },
    viewpoints: ["80 이상: 단기 과열 가능성", "20 이하: 단기 침체 또는 반등 후보", "K/D 교차는 단기 타이밍 참고용"]
  },
  MA5: {
    title: "5일 이동평균선",
    description: "단기 추세를 나타내는 평균 가격",
    interpretation: ({ analysis, ma5 }) => {
      if (ma5 == null) return "5일 이동평균 계산에 필요한 데이터가 부족합니다.";
      return analysis.currentPrice > ma5
        ? `현재가 ${formatPrice(analysis.currentPrice, analysis.currency)} > MA5 ${formatPrice(ma5, analysis.currency)} → 단기 추세 위`
        : `현재가 ${formatPrice(analysis.currentPrice, analysis.currency)} ≤ MA5 ${formatPrice(ma5, analysis.currency)} → 단기 추세 확인 필요`;
    },
    viewpoints: ["단기 추세 판단 기준", "현재가가 MA5 위면 단기 탄력 확인", "MA5 아래면 단기 조정 가능성 확인"]
  },
  MA20: {
    title: "20일 이동평균선",
    description: "중기 추세 기준선",
    interpretation: ({ analysis }) => maInterpretation(analysis, analysis.indicators.ma20, "MA20"),
    viewpoints: ["주요 지지/저항 기준", "현재가가 MA20 위면 단기 추세 유지", "MA20 이탈 시 리스크 관리 우선"]
  },
  MA60: {
    title: "60일 이동평균선",
    description: "중장기 추세 판단",
    interpretation: ({ analysis }) => maInterpretation(analysis, analysis.indicators.ma60, "MA60"),
    viewpoints: ["중장기 추세 방향 확인", "현재가가 MA60 위면 추세 안정성 참고", "MA60 아래면 회복 확인 필요"]
  },
  MA200: {
    title: "200일 이동평균선",
    description: "장기 추세 기준",
    interpretation: ({ analysis }) => maInterpretation(analysis, analysis.indicators.ma200, "MA200"),
    viewpoints: ["장기 상승/하락 기준선", "장기 투자자는 MA200 위치를 중요하게 확인", "MA200 아래에서는 보수적 접근"]
  },
  ATR: {
    title: "ATR",
    description: "변동성 크기를 측정하는 지표",
    interpretation: ({ analysis }) => {
      const value = analysis.indicators.atr;
      if (value == null) return "ATR 데이터가 부족합니다.";
      const percent = analysis.currentPrice ? (value / analysis.currentPrice) * 100 : null;
      return `현재 ATR ${formatPrice(value, analysis.currency)}${percent == null ? "" : ` (${formatNumber(percent, 2)}%)`} → 값이 클수록 변동성 큼`;
    },
    viewpoints: ["값이 클수록 손절/진입 폭을 넓게 봐야 함", "변동성이 커지면 수량과 손절 기준을 더 보수적으로", "ATR은 가격 방향이 아니라 흔들림의 크기"]
  },
  Bollinger: {
    title: "볼린저 밴드",
    description: "가격 변동 범위를 나타냄",
    interpretation: ({ analysis }) => {
      const { bollingerLower, bollingerUpper } = analysis.indicators;
      if (bollingerLower == null || bollingerUpper == null) return "볼린저 밴드 데이터가 부족합니다.";
      if (analysis.currentPrice >= bollingerUpper) return "현재가가 상단 밴드에 근접/돌파 → 과열 가능성 확인";
      if (analysis.currentPrice <= bollingerLower) return "현재가가 하단 밴드에 근접/이탈 → 반등 가능성 또는 약세 지속 확인";
      return "현재가가 밴드 내부 → 변동 범위 안에서 방향성 확인";
    },
    viewpoints: ["상단 근접: 과열 또는 강한 추세", "하단 근접: 반등 가능성 또는 약세", "밴드 확대는 변동성 증가 신호"]
  },
  Volume: {
    title: "거래량 비율",
    description: "최근 거래량 증가 여부",
    interpretation: ({ analysis }) => {
      const value = analysis.indicators.volumeRatio;
      if (value == null) return "거래량 비율 데이터가 부족합니다.";
      if (value > 1.5) return `현재 ${formatNumber(value, 2)}배 → 거래량 증가, 시장 관심 집중`;
      return `현재 ${formatNumber(value, 2)}배 → 평균 수준`;
    },
    viewpoints: ["상승 + 거래량 증가: 신뢰도 개선", "하락 + 거래량 증가: 매도 압력 주의", "거래량 없는 상승은 지속성 확인 필요"]
  },
  ADX: {
    title: "ADX",
    description: "추세 강도를 나타내는 지표",
    interpretation: ({ analysis }) => {
      const value = analysis.indicators.adx;
      if (value == null) return "ADX 데이터가 부족합니다.";
      return value > 25 ? `현재 ADX ${formatNumber(value, 1)} → 강한 추세` : `현재 ADX ${formatNumber(value, 1)} → 약한 추세`;
    },
    viewpoints: ["25 이상: 추세 강도 있음", "20 이하: 방향성 약함", "+DI/-DI와 함께 방향 확인"]
  },
  MFI: {
    title: "MFI",
    description: "거래량 기반 RSI",
    interpretation: ({ analysis }) => {
      const value = analysis.indicators.mfi;
      if (value == null) return "MFI 데이터가 부족합니다.";
      if (value > 80) return `현재 MFI ${formatNumber(value, 1)} → 과열`;
      if (value < 20) return `현재 MFI ${formatNumber(value, 1)} → 과매도`;
      return `현재 MFI ${formatNumber(value, 1)} → 보통`;
    },
    viewpoints: ["80 이상: 자금 흐름 과열", "20 이하: 침체 또는 반등 확인", "가격과 거래량을 함께 반영"]
  },
  OBV: {
    title: "OBV",
    description: "누적 거래량 흐름",
    interpretation: ({ analysis }) => {
      const value = analysis.indicators.obvTrend;
      if (value == null) return "OBV 데이터가 부족합니다.";
      return value > 0 ? `OBV 흐름 ${formatNumber(value, 1)} → 누적 수급 개선` : `OBV 흐름 ${formatNumber(value, 1)} → 수급 확인 필요`;
    },
    viewpoints: ["가격 상승과 OBV 상승이 함께 나오면 수급 확인", "가격 상승인데 OBV 약하면 지속성 점검", "수급 흐름 확인용 보조 지표"]
  },
  SupportResistance: {
    title: "지지/저항",
    description: "최근 가격대에서 매수세와 매도세가 반복된 구간",
    interpretation: ({ item }) => `현재 표시 값 ${item.value} → 단기 가격 반응을 확인할 기준`,
    viewpoints: ["지지선 이탈: 리스크 관리 기준", "저항선 근접: 추격 진입 주의", "돌파/이탈은 거래량과 함께 확인"]
  }
};

export function IndicatorGrid({ analysis }: { analysis: AnalysisResponse }) {
  const i = analysis.indicators;
  const ma5 = calculateMovingAverage(analysis.chart, 5);
  const [selected, setSelected] = useState<IndicatorItem | null>(null);
  const [showCoachmark, setShowCoachmark] = useState(false);

  useEffect(() => {
    try {
      setShowCoachmark(localStorage.getItem("stopro_indicator_help_seen") !== "true");
    } catch {
      setShowCoachmark(false);
    }
  }, []);

  const dismissCoachmark = () => {
    try {
      localStorage.setItem("stopro_indicator_help_seen", "true");
    } catch {
      // localStorage can be unavailable in private or restricted browser modes.
    }
    setShowCoachmark(false);
  };

  const items: IndicatorItem[] = [
    { key: "RSI", label: "RSI", value: formatNumber(i.rsi, 1), note: rsiNote(i.rsi) },
    { key: "MACD", label: "MACD", value: formatNumber(i.macd, 3), note: i.macd && i.macdSignal && i.macd > i.macdSignal ? "강세 전환" : "확인 필요" },
    { key: "Stochastic", label: "Stochastic", value: `${formatNumber(i.stochasticK, 1)} / ${formatNumber(i.stochasticD, 1)}`, note: (i.stochasticK ?? 0) > 85 ? "과열권" : "보통" },
    { key: "MA5", label: "MA5", value: formatPrice(ma5, analysis.currency), note: ma5 == null ? "부족" : analysis.currentPrice > ma5 ? "단기선 위" : "단기선 아래" },
    { key: "MA20", label: "MA20", value: formatPrice(i.ma20, analysis.currency), note: analysis.currentPrice > (i.ma20 ?? Infinity) ? "위에 있음" : "아래에 있음" },
    { key: "MA60", label: "MA60", value: formatPrice(i.ma60, analysis.currency), note: analysis.currentPrice > (i.ma60 ?? Infinity) ? "위에 있음" : "확인 필요" },
    { key: "MA200", label: "MA200", value: formatPrice(i.ma200, analysis.currency), note: analysis.currentPrice > (i.ma200 ?? Infinity) ? "장기 추세 위" : "장기 추세 아래" },
    { key: "ATR", label: "ATR", value: formatPrice(i.atr, analysis.currency), note: "변동성 기준" },
    { key: "Bollinger", label: "Bollinger", value: `${formatPrice(i.bollingerLower, analysis.currency)} ~ ${formatPrice(i.bollingerUpper, analysis.currency)}`, note: "밴드 범위" },
    { key: "Volume", label: "Volume Ratio", value: `${formatNumber(i.volumeRatio, 2)}배`, note: (i.volumeRatio ?? 0) > 1.5 ? "거래량 증가" : "평균권" },
    { key: "ADX", label: "ADX", value: formatNumber(i.adx, 1), note: adxNote(i.adx, i.plusDI, i.minusDI) },
    { key: "MFI", label: "MFI", value: formatNumber(i.mfi, 1), note: mfiNote(i.mfi) },
    { key: "OBV", label: "OBV", value: `${formatNumber(i.obvTrend, 1)}일`, note: (i.obvTrend ?? 0) > 0 ? "누적 수급 개선" : "수급 확인 필요" },
    { key: "SupportResistance", label: "지지/저항", value: `${formatPrice(i.support20, analysis.currency)} / ${formatPrice(i.resistance20, analysis.currency)}`, note: "20일 기준" }
  ];

  return (
    <Card title="기술 지표">
      <div className="mb-3 flex items-center gap-2 rounded-[8px] bg-cardSoft px-3 py-2 text-xs font-bold leading-5 text-subText">
        <Info className="h-4 w-4 shrink-0 text-primary/70" />
        <span>지표가 어렵다면 카드를 눌러 간단 해석을 확인해보세요.</span>
      </div>

      {showCoachmark ? (
        <div className="mb-3 rounded-[8px] border border-primary/15 bg-[#EEF4FF] p-3">
          <div className="flex gap-2.5">
            <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-white text-primary shadow-sm">
              <Info className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-black text-text">지표 카드를 눌러보세요.</p>
              <p className="mt-1 text-xs font-semibold leading-5 text-subText">
                RSI, MACD 같은 지표의 의미와 현재 값 해석을 알려드려요.
              </p>
              <button
                type="button"
                onClick={dismissCoachmark}
                className="mt-2 rounded-full bg-white px-3 py-1.5 text-xs font-black text-primary shadow-sm transition hover:bg-primary hover:text-white active:scale-[0.98]"
              >
                알겠어요
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <div className="grid grid-cols-2 gap-3">
        {items.map((item) => (
          <button
            key={item.label}
            type="button"
            onClick={() => setSelected(item)}
            aria-label={`${item.label} 지표 설명 보기`}
            className="group relative cursor-pointer rounded-[8px] bg-cardSoft p-3 text-left transition duration-200 hover:-translate-y-0.5 hover:bg-white hover:shadow-soft focus:outline-none focus:ring-2 focus:ring-primary/25 active:scale-[0.99]"
          >
            <span
              aria-hidden="true"
              className="absolute right-2.5 top-2.5 flex h-5 w-5 items-center justify-center rounded-full text-subText transition group-hover:bg-white group-hover:text-primary group-active:scale-95"
            >
              <Info className="h-3.5 w-3.5" />
            </span>
            <p className="pr-6 text-[11px] font-bold text-subText">{item.label}</p>
            <p className="mt-1 break-words text-sm font-black text-text">{item.value}</p>
            <p className="mt-1 text-[11px] font-semibold text-subText">{item.note}</p>
          </button>
        ))}
      </div>
      <IndicatorDetailModal item={selected} analysis={analysis} ma5={ma5} onClose={() => setSelected(null)} />
    </Card>
  );
}

function IndicatorDetailModal({
  item,
  analysis,
  ma5,
  onClose
}: {
  item: IndicatorItem | null;
  analysis: AnalysisResponse;
  ma5?: number | null;
  onClose: () => void;
}) {
  if (!item) return null;
  const info = indicatorInfo[item.key];

  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center bg-black/30 px-4 pb-4 sm:items-center sm:pb-0" onClick={onClose}>
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby="indicator-detail-title"
        className="max-h-[78vh] w-full max-w-[430px] overflow-y-auto rounded-t-[16px] border border-border bg-white p-5 shadow-[0_-12px_40px_rgba(15,23,42,0.18)] animate-in slide-in-from-bottom-4 sm:rounded-[12px] sm:shadow-soft"
        onClick={(event) => event.stopPropagation()}
      >
        <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-border sm:hidden" />
        <div className="flex items-start justify-between gap-3">
          <div>
            <p className="text-xs font-black text-primary">지표 설명</p>
            <h3 id="indicator-detail-title" className="mt-1 text-xl font-black text-text">{info.title}</h3>
          </div>
          <button type="button" onClick={onClose} aria-label="닫기" className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-cardSoft text-subText active:bg-border">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="mt-5 space-y-4">
          <InfoBlock title="정의" body={info.description} />
          <InfoBlock title="현재 상태 해석" body={info.interpretation({ analysis, item, ma5 })} />
          <div className="rounded-[8px] bg-cardSoft p-4">
            <p className="text-xs font-black text-subText">투자 관점</p>
            <ul className="mt-2 space-y-2">
              {info.viewpoints.map((point) => (
                <li key={point} className="flex gap-2 text-sm leading-6 text-text">
                  <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/60" />
                  <span>{point}</span>
                </li>
              ))}
            </ul>
          </div>
          <p className="rounded-[8px] bg-warning/10 p-3 text-xs font-bold leading-5 text-subText">
            이 지표 하나만으로 판단하지 말고, 추세·거래량·지지/저항과 함께 확인하세요.
          </p>
        </div>
      </div>
    </div>
  );
}

function InfoBlock({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-[8px] border border-border bg-white p-4">
      <p className="text-xs font-black text-subText">{title}</p>
      <p className="mt-2 text-sm font-semibold leading-6 text-text">{body}</p>
    </div>
  );
}

function maInterpretation(analysis: AnalysisResponse, value: number | null | undefined, label: string) {
  if (value == null) return `${label} 데이터가 부족합니다.`;
  return analysis.currentPrice > value
    ? `현재가 ${formatPrice(analysis.currentPrice, analysis.currency)} > ${label} ${formatPrice(value, analysis.currency)} → 추세 기준선 위`
    : `현재가 ${formatPrice(analysis.currentPrice, analysis.currency)} ≤ ${label} ${formatPrice(value, analysis.currency)} → 추세 회복 확인 필요`;
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
