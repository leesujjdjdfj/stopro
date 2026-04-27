import { Gauge } from "lucide-react";
import { Card } from "@/components/common/Card";
import { formatNumber } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function RewardRiskCard({ analysis }: { analysis: AnalysisResponse }) {
  const rr = analysis.rewardRisk;
  const weak = (rr.ratioToSecondTarget ?? 0) < 1.5;
  return (
    <Card className={weak ? "border-warning/30" : "border-safe/30"}>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold text-subText">손익비 R:R</p>
          <p className={`mt-1 text-3xl font-black ${weak ? "text-warning" : "text-safe"}`}>{formatNumber(rr.ratioToSecondTarget, 2)}</p>
        </div>
        <Gauge className={`h-8 w-8 ${weak ? "text-warning" : "text-safe"}`} />
      </div>
      <p className="mt-2 text-sm font-bold text-text">{rr.label}</p>
      <p className="mt-2 text-sm leading-6 text-subText">{rr.description}</p>
      {weak && <p className="mt-3 rounded-[8px] bg-warning/10 p-3 text-sm font-bold text-amber-700">신규 진입 매력 낮음</p>}
    </Card>
  );
}
