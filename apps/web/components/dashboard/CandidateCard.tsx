import Link from "next/link";
import { ArrowUpRight } from "lucide-react";
import { Card } from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { formatNumber, formatPercent } from "@/lib/format";
import type { WatchlistSignal } from "@/types/analysis";

export function CandidateCard({ candidates }: { candidates: WatchlistSignal[] }) {
  return (
    <Card title="우선 확인 후보">
      {candidates.length === 0 ? (
        <p className="text-sm leading-6 text-subText">현재 조건에서는 우선 확인할 매수 후보가 많지 않습니다.</p>
      ) : (
        <div className="space-y-3">
          {candidates.map((item) => (
            <Link key={item.ticker} href={`/analyze?ticker=${item.ticker}`} className="flex items-center justify-between rounded-[8px] bg-safe/10 p-4">
              <div>
                <div className="flex items-center gap-2">
                  <p className="font-black text-text">{item.ticker}</p>
                  <Badge tone="green">{item.decisionLabel}</Badge>
                </div>
                <p className="mt-1 text-sm text-subText">손익비 {formatNumber(item.rewardRiskRatio, 2)} · 등락 {formatPercent(item.dailyChangePercent)}</p>
              </div>
              <ArrowUpRight className="h-5 w-5 text-safe" />
            </Link>
          ))}
        </div>
      )}
    </Card>
  );
}
