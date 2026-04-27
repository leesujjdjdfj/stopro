import { ShieldAlert } from "lucide-react";
import { Card } from "@/components/common/Card";
import { toneForRisk } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function RiskScoreCard({ analysis }: { analysis: AnalysisResponse }) {
  const score = analysis.risk.score;
  return (
    <Card title="리스크 점수">
      <div className="flex items-center gap-4">
        <div className="relative h-24 w-24 shrink-0">
          <div className="absolute inset-0 rounded-full bg-cardSoft" />
          <div
            className="absolute inset-0 rounded-full"
            style={{ background: `conic-gradient(#4F7CFF ${score * 3.6}deg, #E5E7EB 0deg)` }}
          />
          <div className="absolute inset-2 flex items-center justify-center rounded-full bg-white">
            <span className={`text-2xl font-black ${toneForRisk(score)}`}>{score}</span>
          </div>
        </div>
        <div>
          <div className="flex items-center gap-2">
            <ShieldAlert className={`h-5 w-5 ${toneForRisk(score)}`} />
            <p className="font-black text-text">{analysis.risk.label}</p>
          </div>
          <p className="mt-2 text-sm leading-6 text-subText">{analysis.risk.description}</p>
        </div>
      </div>
      <div className="mt-4 space-y-2">
        {analysis.risk.factors.map((factor) => (
          <div key={factor.name} className="rounded-[8px] bg-cardSoft p-3">
            <div className="flex items-center justify-between gap-3">
              <p className="text-sm font-bold text-text">{factor.name}</p>
              <p className={`text-sm font-black ${toneForRisk(factor.score * 4)}`}>{factor.score}</p>
            </div>
            <p className="mt-1 text-xs leading-5 text-subText">{factor.description}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
