import Link from "next/link";
import { Search, Trash2 } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card } from "@/components/common/Card";
import { StockIdentity } from "@/components/common/StockIdentity";
import { formatDateTime, formatNumber, toneForRisk } from "@/lib/format";
import type { WatchlistItem } from "@/types/portfolio";

export function WatchlistTable({ items, onDelete }: { items: WatchlistItem[]; onDelete: (ticker: string) => void }) {
  return (
    <Card title="관심종목">
      <div className="space-y-3">
        {items.map((item) => (
          <div key={item.ticker} className="rounded-[8px] border border-border p-4">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <StockIdentity stock={item} nameClassName="text-lg font-black text-text" />
                {item.note && <p className="mt-1 text-sm leading-6 text-subText">{item.note}</p>}
              </div>
              {item.last_decision && <Badge tone={item.last_decision === "candidate" || item.last_decision === "split_buy" ? "green" : item.last_decision === "caution" || item.last_decision === "avoid" ? "red" : "orange"}>{item.last_decision}</Badge>}
            </div>
            <div className="mt-4 grid grid-cols-3 gap-2">
              <Mini label="리스크" value={String(item.last_risk_score ?? "-")} className={toneForRisk(item.last_risk_score)} />
              <Mini label="손익비" value={formatNumber(item.last_reward_risk_ratio, 2)} />
              <Mini label="최근 분석" value={formatDateTime(item.last_analyzed_at)} />
            </div>
            <div className="mt-4 grid grid-cols-[1fr_auto] gap-2">
              <Link href={`/analyze?ticker=${item.ticker}`} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-[8px] bg-primary px-4 text-sm font-bold text-white">
                <Search className="h-4 w-4" />
                분석하기
              </Link>
              <Button variant="secondary" onClick={() => onDelete(item.ticker)} title="삭제">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function Mini({ label, value, className = "" }: { label: string; value: string; className?: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className={`mt-1 break-words text-xs font-black ${className || "text-text"}`}>{value}</p>
    </div>
  );
}
