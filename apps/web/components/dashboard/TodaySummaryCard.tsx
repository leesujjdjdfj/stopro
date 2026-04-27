import { AlertTriangle, BellRing, BriefcaseBusiness, Star } from "lucide-react";
import { Card } from "@/components/common/Card";
import type { DashboardResponse } from "@/types/analysis";

export function TodaySummaryCard({ data }: { data: DashboardResponse }) {
  const items = [
    { label: "관심종목", value: data.watchlistCount, icon: Star, tone: "text-primary" },
    { label: "매수 후보", value: data.candidateCount, icon: BriefcaseBusiness, tone: "text-safe" },
    { label: "주의 종목", value: data.cautionCount, icon: AlertTriangle, tone: "text-warning" },
    { label: "발생 알림", value: data.triggeredAlertCount, icon: BellRing, tone: "text-danger" }
  ];
  return (
    <Card>
      <div className="grid grid-cols-4 gap-2">
        {items.map(({ label, value, icon: Icon, tone }) => (
          <div key={label} className="rounded-[8px] bg-cardSoft p-3">
            <Icon className={`h-4 w-4 ${tone}`} />
            <p className="mt-3 text-2xl font-black text-text">{value}</p>
            <p className="mt-1 text-[11px] font-bold text-subText">{label}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
