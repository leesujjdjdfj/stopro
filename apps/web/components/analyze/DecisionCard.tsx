import { CheckCircle2, CircleDashed, OctagonAlert, PauseCircle } from "lucide-react";
import { Card } from "@/components/common/Card";
import type { AnalysisResponse } from "@/types/analysis";

const iconMap = {
  candidate: CheckCircle2,
  split_buy: CircleDashed,
  watch: PauseCircle,
  caution: OctagonAlert,
  avoid: OctagonAlert
};

export function DecisionCard({ analysis }: { analysis: AnalysisResponse }) {
  const Icon = iconMap[analysis.decision.status];
  const isRisk = analysis.decision.status === "caution" || analysis.decision.status === "avoid";
  const suitability = analysis.decision.buySuitability;
  const percent = suitability?.percent ?? analysis.decision.buySuitabilityPercent ?? analysis.decision.score;
  return (
    <Card>
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold text-subText">투자 판단 보조</p>
          <p className={`mt-1 text-3xl font-black ${isRisk ? "text-danger" : "text-primary"}`}>{analysis.decision.label}</p>
        </div>
        <Icon className={`h-9 w-9 ${isRisk ? "text-danger" : "text-primary"}`} />
      </div>
      <div className="mt-5 rounded-[8px] bg-cardSoft p-4">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-xs font-bold text-subText">분석상 매수 적합도</p>
            <p className={`mt-1 text-3xl font-black ${suitabilityTone(percent)}`}>{percent}%</p>
          </div>
          <p className="rounded-full bg-white px-3 py-1 text-xs font-black text-subText">{suitability?.label ?? "조건 점수"}</p>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-border">
          <div className={`h-full rounded-full ${suitabilityBar(percent)}`} style={{ width: `${Math.max(0, Math.min(100, percent))}%` }} />
        </div>
        {suitability?.factors?.length ? (
          <div className="mt-4 grid grid-cols-5 gap-1.5">
            {suitability.factors.map((factor) => (
              <div key={factor.name} className="min-w-0">
                <div className="h-1.5 overflow-hidden rounded-full bg-white">
                  <div className="h-full rounded-full bg-primary" style={{ width: `${Math.round((factor.score / factor.maxScore) * 100)}%` }} />
                </div>
                <p className="mt-1 truncate text-[10px] font-bold text-subText">{factor.name}</p>
              </div>
            ))}
          </div>
        ) : null}
        <p className="mt-3 text-xs leading-5 text-subText">
          {suitability?.description ?? "현재 지표 조건을 0~100으로 환산한 참고 점수입니다."}
        </p>
      </div>
      <p className="mt-4 text-sm leading-6 text-subText">{analysis.decision.reason}</p>
      <p className="mt-3 rounded-[8px] bg-cardSoft p-3 text-xs leading-5 text-subText">
        {suitability?.note ?? "“매수 후보”는 매수 권유가 아니라 분석상 조건이 상대적으로 양호하다는 뜻입니다."}
      </p>
    </Card>
  );
}

function suitabilityTone(percent: number) {
  if (percent >= 75) return "text-safe";
  if (percent >= 60) return "text-primary";
  if (percent >= 45) return "text-warning";
  return "text-danger";
}

function suitabilityBar(percent: number) {
  if (percent >= 75) return "bg-safe";
  if (percent >= 60) return "bg-primary";
  if (percent >= 45) return "bg-warning";
  return "bg-danger";
}
