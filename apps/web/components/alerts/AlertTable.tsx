import { Trash2 } from "lucide-react";
import { Badge } from "@/components/common/Badge";
import { Button } from "@/components/common/Button";
import { Card } from "@/components/common/Card";
import { formatDateTime, formatNumber } from "@/lib/format";
import type { AlertItem } from "@/types/portfolio";
import type { TriggeredAlert } from "@/types/analysis";

export function AlertTable({ alerts, triggered, onDelete }: { alerts: AlertItem[]; triggered: TriggeredAlert[]; onDelete: (id: number) => void }) {
  const triggeredIds = new Set(triggered.map((item) => item.id));
  return (
    <Card title="알림 조건">
      <div className="space-y-3">
        {alerts.map((item) => {
          const isTriggered = triggeredIds.has(item.id);
          return (
            <div key={item.id} className={`rounded-[8px] border p-4 ${isTriggered ? "border-danger/30 bg-danger/10" : "border-border"}`}>
              <div className="flex items-start justify-between gap-3">
                <div>
                  <div className="flex items-center gap-2">
                    <p className="text-lg font-black text-text">{item.ticker}</p>
                    <Badge tone={isTriggered ? "red" : item.is_active ? "green" : "gray"}>{isTriggered ? "충족" : item.is_active ? "활성" : "비활성"}</Badge>
                  </div>
                  <p className="mt-1 text-sm text-subText">{item.condition_type} · {formatNumber(item.target_price, 2)}</p>
                </div>
                <Button variant="secondary" onClick={() => onDelete(item.id)} title="삭제">
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
              {item.message && <p className="mt-3 rounded-[8px] bg-white/70 p-3 text-sm leading-6 text-subText">{item.message}</p>}
              <p className="mt-3 text-xs text-subText">생성 {formatDateTime(item.created_at)}</p>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
