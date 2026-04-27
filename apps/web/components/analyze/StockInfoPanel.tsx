import { Card } from "@/components/common/Card";
import { StockIdentity } from "@/components/common/StockIdentity";
import { formatDateTime, formatNumber, formatPrice } from "@/lib/format";
import type { AnalysisResponse, ChartPoint } from "@/types/analysis";

export function StockInfoPanel({ analysis }: { analysis: AnalysisResponse }) {
  const latest = getLatestOhlc(analysis.chart);
  const fundamentals = analysis.fundamentals;

  return (
    <Card title="종목 정보">
      <StockIdentity stock={analysis} className="mb-4" nameClassName="text-lg font-black text-text" />
      <div className="grid grid-cols-2 gap-3">
        <Metric label="시가" value={formatPrice(latest?.open, analysis.currency)} />
        <Metric label="고가" value={formatPrice(latest?.high, analysis.currency)} valueClassName="text-up" />
        <Metric label="저가" value={formatPrice(latest?.low, analysis.currency)} valueClassName="text-down" />
        <Metric label="종가" value={formatPrice(latest?.close ?? analysis.currentPrice, analysis.currency)} />
        <Metric label="거래량" value={formatNumber(analysis.quote.volume ?? latest?.volume, 0)} />
        <Metric label="평균 거래량" value={formatNumber(analysis.quote.averageVolume, 0)} />
        <Metric label="시가총액" value={formatNumber(fundamentals.marketCap, 0)} />
        <Metric label="PER / Forward" value={`${formatNumber(fundamentals.trailingPE, 2)} / ${formatNumber(fundamentals.forwardPE, 2)}`} />
        <Metric label="PBR" value="-" />
        <Metric label="EPS" value={formatNumber(fundamentals.eps, 2)} />
      </div>
      <p className="mt-4 text-xs leading-5 text-subText">
        기준 {formatDateTime(analysis.dataTimestamp)} · 무료 데이터 특성상 실제 체결가와 차이가 있을 수 있습니다.
      </p>
    </Card>
  );
}

function Metric({ label, value, valueClassName = "text-text" }: { label: string; value: string; valueClassName?: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className={`mt-1 break-words text-sm font-black ${valueClassName}`}>{value}</p>
    </div>
  );
}

function getLatestOhlc(chart: ChartPoint[]) {
  return [...chart]
    .reverse()
    .find((point) => point.open != null && point.high != null && point.low != null && point.close != null);
}
