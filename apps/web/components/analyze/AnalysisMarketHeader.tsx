import { Activity, ShieldAlert, TrendingUp } from "lucide-react";
import type { ReactNode } from "react";
import { Badge } from "@/components/common/Badge";
import { StockIdentity } from "@/components/common/StockIdentity";
import { formatNumber, formatPercent, formatPrice, toneForChange, toneForRisk } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function AnalysisMarketHeader({ analysis }: { analysis: AnalysisResponse }) {
  const rr = analysis.rewardRisk.ratioToSecondTarget ?? analysis.rewardRisk.ratioToFirstTarget;

  return (
    <section className="rounded-[8px] border border-border bg-card p-5 shadow-soft">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <Badge tone={analysis.decision.status === "candidate" ? "green" : analysis.decision.status === "caution" || analysis.decision.status === "avoid" ? "red" : "orange"}>
            {analysis.decision.label}
          </Badge>
          <StockIdentity stock={analysis} className="mt-3" nameClassName="text-xl font-black leading-tight text-text" />
        </div>
        <div className="shrink-0 text-right">
          <p className="text-2xl font-black tracking-normal text-text">{formatPrice(analysis.currentPrice, analysis.currency)}</p>
          <p className={`mt-1 text-sm font-black ${toneForChange(analysis.dailyChangePercent)}`}>{formatPercent(analysis.dailyChangePercent)}</p>
        </div>
      </div>

      <div className="mt-5 grid grid-cols-3 gap-2">
        <CompactMetric icon={<TrendingUp className="h-4 w-4" />} label="손익비" value={rr == null ? "-" : `${formatNumber(rr, 2)}R`} />
        <CompactMetric icon={<ShieldAlert className="h-4 w-4" />} label="리스크" value={`${analysis.risk.score}점`} valueClassName={toneForRisk(analysis.risk.score)} />
        <CompactMetric icon={<Activity className="h-4 w-4" />} label="적합도" value={`${analysis.decision.buySuitability?.percent ?? analysis.decision.buySuitabilityPercent ?? analysis.decision.score}%`} />
      </div>
    </section>
  );
}

function CompactMetric({
  icon,
  label,
  value,
  valueClassName = "text-text"
}: {
  icon: ReactNode;
  label: string;
  value: string;
  valueClassName?: string;
}) {
  return (
    <div className="min-w-0 rounded-[8px] bg-cardSoft p-3">
      <div className="flex items-center gap-1.5 text-subText">
        {icon}
        <p className="truncate text-[11px] font-bold">{label}</p>
      </div>
      <p className={`mt-1 truncate text-sm font-black ${valueClassName}`}>{value}</p>
    </div>
  );
}
