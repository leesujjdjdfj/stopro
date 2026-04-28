import { Sparkles } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Card } from "@/components/common/Card";
import { StockIdentity } from "@/components/common/StockIdentity";
import type { AnalysisResponse } from "@/types/analysis";

export function AiSummaryCard({ analysis }: { analysis: AnalysisResponse }) {
  const insight = analysis.investmentInsight;
  const label = insight?.finalLabel ?? analysis.decision.label;
  const summary = insight?.oneLine ?? analysis.summary;
  const badgeTone = insight
    ? insight.tone === "positive"
      ? "green"
      : insight.tone === "danger" || insight.tone === "warning"
        ? "red"
        : "orange"
    : analysis.decision.status === "candidate"
      ? "green"
      : analysis.decision.status === "caution" || analysis.decision.status === "avoid"
        ? "red"
        : "orange";
  return (
    <Card className="border-primary/20 bg-gradient-to-b from-white to-blue-50">
      <div className="flex items-start gap-3">
        <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-[8px] bg-primary text-white">
          <Sparkles className="h-5 w-5" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2">
            <Badge tone={badgeTone}>{label}</Badge>
            {insight ? <span className="text-xs font-black text-subText">{insight.totalScore}점</span> : null}
          </div>
          <StockIdentity stock={analysis} className="mt-2" nameClassName="text-lg font-black text-text" />
          <p className="mt-3 text-[15px] font-semibold leading-7 text-text">{summary}</p>
        </div>
      </div>
    </Card>
  );
}
