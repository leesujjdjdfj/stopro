import { Card } from "@/components/common/Card";
import { formatPrice } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function StrategyPlanCard({ analysis }: { analysis: AnalysisResponse }) {
  const s = analysis.strategy;
  return (
    <Card title="가격 기준 전략">
      <p className="mb-4 rounded-[8px] bg-cardSoft p-3 text-sm font-semibold leading-6 text-text">{s.message}</p>
      <div className="grid grid-cols-2 gap-3">
        <Metric label="진입 기준가" value={formatPrice(s.entryPrice, analysis.currency)} />
        <Metric label="손절 기준가" value={formatPrice(s.stopLoss, analysis.currency)} danger />
        <Metric label="1차 매수 구간" value={formatPrice(s.firstBuyZone, analysis.currency)} />
        <Metric label="2차 매수 구간" value={formatPrice(s.secondBuyZone, analysis.currency)} />
        <Metric label="1차 목표가" value={formatPrice(s.firstTarget, analysis.currency)} />
        <Metric label="2차 목표가" value={formatPrice(s.secondTarget, analysis.currency)} />
      </div>
      <div className="mt-4 space-y-2">
        {s.plan.map((step) => (
          <div key={`${step.step}-${step.condition}`} className="flex gap-3 rounded-[8px] border border-border p-3">
            <strong className="w-10 shrink-0 text-sm text-primary">{step.step}</strong>
            <div className="min-w-0">
              <p className="text-sm font-semibold leading-5 text-text">{step.condition}</p>
              <p className="mt-1 text-xs text-subText">비중 {step.weight}%</p>
            </div>
          </div>
        ))}
      </div>
      <p className="mt-4 text-xs leading-5 text-subText">무효화 조건: {s.invalidationCondition}</p>
    </Card>
  );
}

function Metric({ label, value, danger }: { label: string; value: string; danger?: boolean }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className={`mt-1 text-base font-black ${danger ? "text-danger" : "text-text"}`}>{value}</p>
    </div>
  );
}
