import { Card } from "@/components/common/Card";
import { StockIdentity } from "@/components/common/StockIdentity";
import { formatDateTime, formatNumber, formatPercent, formatPrice, toneForChange } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function QuoteCard({ analysis }: { analysis: AnalysisResponse }) {
  return (
    <Card title="시세">
      <div className="flex items-end justify-between gap-3">
        <div>
          <StockIdentity stock={analysis} nameClassName="text-sm font-black text-subText" />
          <p className="mt-1 text-3xl font-black text-text">{formatPrice(analysis.currentPrice, analysis.currency)}</p>
        </div>
        <p className={`text-lg font-black ${toneForChange(analysis.dailyChangePercent)}`}>{formatPercent(analysis.dailyChangePercent)}</p>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <Metric label="거래량" value={formatNumber(analysis.quote.volume, 0)} />
        <Metric label="평균 거래량" value={formatNumber(analysis.quote.averageVolume, 0)} />
        <Metric label="52주 고점" value={formatPrice(analysis.quote.fiftyTwoWeekHigh, analysis.currency)} />
        <Metric label="52주 저점" value={formatPrice(analysis.quote.fiftyTwoWeekLow, analysis.currency)} />
      </div>
      <p className="mt-4 text-xs leading-5 text-subText">
        기준 {formatDateTime(analysis.dataTimestamp)} · {analysis.cacheHit ? "캐시 사용" : "신규 조회"}
      </p>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className="mt-1 font-black text-text">{value}</p>
    </div>
  );
}
