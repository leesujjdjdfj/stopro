import Link from "next/link";
import { ChevronRight } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Card } from "@/components/common/Card";
import { StockIdentity } from "@/components/common/StockIdentity";
import { formatDateTime, formatNumber, formatPercent, toneForChange, toneForRisk } from "@/lib/format";
import type { WatchlistSignal } from "@/types/analysis";

function decisionTone(decision: string) {
  if (decision === "candidate" || decision === "split_buy") return "green";
  if (decision === "caution" || decision === "avoid") return "red";
  return "orange";
}

export function WatchlistSignalTable({ signals }: { signals: WatchlistSignal[] }) {
  return (
    <Card title="관심종목 신호">
      <div className="space-y-3">
        {signals.map((item) => (
          <Link
            href={`/analyze?ticker=${item.ticker}`}
            key={item.ticker}
            className="block rounded-[8px] border border-border bg-white p-4 active:bg-cardSoft"
          >
            <div className="flex items-center justify-between gap-3">
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <StockIdentity stock={item} className="flex-1" />
                  <Badge tone={decisionTone(item.decision)}>{item.decisionLabel}</Badge>
                </div>
              </div>
              <ChevronRight className="h-5 w-5 shrink-0 text-subText" />
            </div>
            <div className="mt-4 grid grid-cols-4 gap-2 text-sm">
              <div>
                <p className="text-[11px] font-bold text-subText">현재가</p>
                <p className="font-bold text-text">{formatNumber(item.price, 2)}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold text-subText">등락</p>
                <p className={`font-bold ${toneForChange(item.dailyChangePercent)}`}>{formatPercent(item.dailyChangePercent)}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold text-subText">리스크</p>
                <p className={`font-bold ${toneForRisk(item.riskScore)}`}>{item.riskScore ?? "-"}</p>
              </div>
              <div>
                <p className="text-[11px] font-bold text-subText">손익비</p>
                <p className="font-bold text-text">{formatNumber(item.rewardRiskRatio, 2)}</p>
              </div>
            </div>
            <p className="mt-3 text-[11px] text-subText">분석 기준 {formatDateTime(item.lastAnalyzedAt)}</p>
          </Link>
        ))}
      </div>
    </Card>
  );
}
