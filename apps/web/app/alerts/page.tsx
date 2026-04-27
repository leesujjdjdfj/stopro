"use client";

import { useCallback, useEffect, useState } from "react";
import { RefreshCw } from "lucide-react";
import { AlertForm } from "@/components/alerts/AlertForm";
import { AlertTable } from "@/components/alerts/AlertTable";
import { Button } from "@/components/common/Button";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { api } from "@/lib/api";
import type { TriggeredAlert } from "@/types/analysis";
import type { AlertItem } from "@/types/portfolio";

export default function AlertsPage() {
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [triggered, setTriggered] = useState<TriggeredAlert[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const [alertItems, triggeredItems] = await Promise.all([api.getAlerts(), api.getTriggeredAlerts()]);
      setAlerts(alertItems);
      setTriggered(triggeredItems);
    } catch (err) {
      setError(err instanceof Error ? err.message : "알림 조건을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  if (loading) return <LoadingSkeleton rows={4} />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="space-y-4">
      <AlertForm
        loading={saving}
        onAdd={async (payload) => {
          setSaving(true);
          await api.addAlert(payload);
          setSaving(false);
          await load();
        }}
      />
      <Button className="w-full" variant="secondary" onClick={load}>
        <RefreshCw className="h-4 w-4" />
        조건 충족 확인
      </Button>
      {alerts.length === 0 ? (
        <EmptyState title="가격 알림 조건이 없습니다" description="앱을 열었을 때 현재가가 저장한 조건을 충족했는지 확인합니다. 실제 푸시 알림은 포함하지 않습니다." />
      ) : (
        <AlertTable
          alerts={alerts}
          triggered={triggered}
          onDelete={async (id) => {
            await api.deleteAlert(id);
            await load();
          }}
        />
      )}
    </div>
  );
}
