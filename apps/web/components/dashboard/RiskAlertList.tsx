import Link from "next/link";
import { AlertTriangle } from "lucide-react";
import { Card } from "@/components/common/Card";
import { formatNumber, toneForRisk } from "@/lib/format";
import type { TriggeredAlert, WatchlistSignal } from "@/types/analysis";

export function RiskAlertList({ riskAlerts, triggeredAlerts }: { riskAlerts: WatchlistSignal[]; triggeredAlerts: TriggeredAlert[] }) {
  return (
    <Card title="리스크 알림">
      <div className="space-y-3">
        {triggeredAlerts.map((alert) => (
          <div key={`alert-${alert.id}`} className="rounded-[8px] border border-danger/20 bg-danger/10 p-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-danger" />
              <p className="font-bold text-danger">{alert.ticker} 알림 조건 충족</p>
            </div>
            <p className="mt-1 text-sm text-subText">{alert.message || `${alert.conditionType} ${formatNumber(alert.targetPrice, 2)}`}</p>
          </div>
        ))}
        {riskAlerts.map((item) => (
          <Link key={item.ticker} href={`/analyze?ticker=${item.ticker}`} className="block rounded-[8px] border border-warning/25 bg-warning/10 p-4">
            <p className="font-black text-text">{item.ticker}</p>
            <p className="mt-1 text-sm text-subText">
              {item.priceBelowMA20 ? "MA20 아래로 내려와 추세 약화 확인 필요" : "위험 점수가 높아 리스크 관리 필요"}
            </p>
            <p className={`mt-2 text-sm font-black ${toneForRisk(item.riskScore)}`}>리스크 점수 {item.riskScore ?? "-"}</p>
          </Link>
        ))}
        {riskAlerts.length === 0 && triggeredAlerts.length === 0 && (
          <p className="text-sm leading-6 text-subText">현재 저장된 조건 기준으로 즉시 확인할 위험 알림은 없습니다.</p>
        )}
      </div>
    </Card>
  );
}
