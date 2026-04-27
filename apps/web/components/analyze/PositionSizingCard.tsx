import { Card } from "@/components/common/Card";
import { formatKRW, formatNumber } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function PositionSizingCard({ analysis }: { analysis: AnalysisResponse }) {
  const p = analysis.positionSizing;
  return (
    <Card title="포지션 사이징">
      <div className="grid grid-cols-2 gap-3">
        <Metric label="투자금" value={formatKRW(p.capitalKRW)} />
        <Metric label="허용 리스크" value={`${p.riskPercent}% (${formatKRW(p.riskAmountKRW)})`} />
        <Metric label="1주당 위험" value={formatKRW(p.riskPerShareKRW)} />
        <Metric label="권장 수량" value={`${p.quantity}주`} strong />
        <Metric label="예상 사용금액" value={formatKRW(p.estimatedCapitalKRW)} />
        <Metric label="남는 현금" value={formatKRW(p.remainingCashKRW)} />
      </div>
      {p.warning && <p className="mt-4 rounded-[8px] bg-warning/10 p-3 text-sm font-semibold leading-6 text-amber-700">{p.warning}</p>}
      {p.quantity === 0 && p.referenceQuantity ? <p className="mt-2 text-xs text-subText">참고 최소 수량: {formatNumber(p.referenceQuantity, 0)}주</p> : null}
    </Card>
  );
}

function Metric({ label, value, strong }: { label: string; value: string; strong?: boolean }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className={`mt-1 ${strong ? "text-2xl" : "text-sm"} font-black text-text`}>{value}</p>
    </div>
  );
}
