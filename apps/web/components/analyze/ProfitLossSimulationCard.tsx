import { Card } from "@/components/common/Card";
import { formatKRW, formatPercent } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function ProfitLossSimulationCard({ analysis }: { analysis: AnalysisResponse }) {
  const p = analysis.profitLoss;
  return (
    <Card title="손익 시뮬레이션">
      <div className="grid grid-cols-3 gap-2">
        <Box label="1차 목표" value={formatKRW(p.firstTargetProfitKRW)} percent={formatPercent(p.firstTargetReturnPercent)} tone="text-up" />
        <Box label="2차 목표" value={formatKRW(p.secondTargetProfitKRW)} percent={formatPercent(p.secondTargetReturnPercent)} tone="text-up" />
        <Box label="손절" value={formatKRW(p.stopLossLossKRW)} percent={formatPercent(p.stopLossReturnPercent)} tone="text-down" />
      </div>
    </Card>
  );
}

function Box({ label, value, percent, tone }: { label: string; value: string; percent: string; tone: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className={`mt-2 text-sm font-black ${tone}`}>{value}</p>
      <p className={`mt-1 text-xs font-bold ${tone}`}>{percent}</p>
    </div>
  );
}
