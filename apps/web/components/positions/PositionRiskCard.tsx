import { AlertTriangle, ShieldCheck } from "lucide-react";
import { Card } from "@/components/common/Card";
import type { PositionItem } from "@/types/portfolio";

export function PositionRiskCard({ positions }: { positions: PositionItem[] }) {
  const risky = positions.filter((item) => item.riskState && item.riskState !== "보통");
  return (
    <Card title="보유 종목 리스크">
      {risky.length === 0 ? (
        <div className="flex gap-3 rounded-[8px] bg-safe/10 p-4 text-safe">
          <ShieldCheck className="h-5 w-5 shrink-0" />
          <p className="text-sm font-bold leading-6">현재 입력한 기준에서는 즉시 확인할 위험 신호가 크지 않습니다.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {risky.map((item) => (
            <div key={item.id} className="rounded-[8px] bg-warning/10 p-4">
              <div className="flex items-center gap-2 text-warning">
                <AlertTriangle className="h-4 w-4" />
                <p className="font-black">{item.ticker} · {item.riskState}</p>
              </div>
              <ul className="mt-2 space-y-1 text-sm leading-6 text-subText">
                {(item.riskReasons ?? []).map((reason) => (
                  <li key={reason}>{reason}</li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      )}
    </Card>
  );
}
