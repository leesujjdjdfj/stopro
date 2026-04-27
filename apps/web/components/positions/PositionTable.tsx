import Link from "next/link";
import { Search, Trash2 } from "lucide-react";
import { Button } from "@/components/common/Button";
import { Card } from "@/components/common/Card";
import { formatNumber, formatPercent, formatPrice, toneForChange } from "@/lib/format";
import type { PositionItem } from "@/types/portfolio";

export function PositionTable({ positions, onDelete }: { positions: PositionItem[]; onDelete: (id: number) => void }) {
  return (
    <Card title="보유 목록">
      <div className="space-y-3">
        {positions.map((item) => (
          <div key={item.id} className="rounded-[8px] border border-border p-4">
            <div className="flex items-start justify-between gap-3">
              <div>
                <p className="text-lg font-black text-text">{item.ticker}</p>
                <p className="mt-1 text-sm text-subText">평균 {formatNumber(item.average_price, 2)} · {formatNumber(item.quantity, 0)}주</p>
              </div>
              <p className={`text-right text-sm font-black ${item.riskState === "보통" ? "text-safe" : "text-warning"}`}>{item.riskState ?? "확인 중"}</p>
            </div>
            <div className="mt-4 grid grid-cols-2 gap-3">
              <Metric label="현재가" value={formatNumber(item.currentPrice, 2)} />
              <Metric label="평가금액" value={formatNumber(item.currentValue, 0)} />
              <Metric label="평가손익" value={formatNumber(item.profitLoss, 0)} className={toneForChange(item.profitLoss)} />
              <Metric label="수익률" value={formatPercent(item.profitLossPercent)} className={toneForChange(item.profitLossPercent)} />
              <Metric label="손절가까지" value={formatPercent(item.stopDistancePercent)} />
              <Metric label="목표가까지" value={formatPercent(item.targetDistancePercent)} />
            </div>
            {item.note && <p className="mt-3 rounded-[8px] bg-cardSoft p-3 text-sm leading-6 text-subText">{item.note}</p>}
            <div className="mt-4 grid grid-cols-[1fr_auto] gap-2">
              <Link href={`/analyze?ticker=${item.ticker}`} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-[8px] bg-primary px-4 text-sm font-bold text-white">
                <Search className="h-4 w-4" />
                분석하기
              </Link>
              <Button variant="secondary" onClick={() => onDelete(item.id)} title="삭제">
                <Trash2 className="h-4 w-4" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

function Metric({ label, value, className = "text-text" }: { label: string; value: string; className?: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className={`mt-1 text-sm font-black ${className}`}>{value}</p>
    </div>
  );
}
