import { Card } from "@/components/common/Card";
import { formatPercent } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function BacktestSummaryCard({ analysis }: { analysis: AnalysisResponse }) {
  const b = analysis.backtest;
  return (
    <Card title="백테스트 요약">
      <div className="grid grid-cols-2 gap-3">
        <Metric label="발생 횟수" value={`${b.sampleCount}회`} />
        <Metric label="승률" value={formatPercent(b.winRate).replace("+", "")} />
        <Metric label="평균 수익률" value={formatPercent(b.averageReturnPercent)} />
        <Metric label="최대 손실" value={formatPercent(b.maxLossPercent)} />
        <Metric label="평균 보유" value={`${b.averageHoldingDays}일`} />
        <Metric label="신뢰도" value={b.reliability} />
      </div>
      <p className="mt-4 text-xs leading-5 text-subText">백테스트는 과거 규칙 검증이며 미래 수익을 보장하지 않습니다.</p>
      {b.warning && <p className="mt-3 rounded-[8px] bg-warning/10 p-3 text-sm font-bold text-amber-700">{b.warning}</p>}
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className="mt-1 text-sm font-black text-text">{value}</p>
    </div>
  );
}
