"use client";

import type { ReactNode } from "react";
import { useCallback, useEffect, useState } from "react";
import { Database, RefreshCw, Save, Trash2 } from "lucide-react";
import { Button } from "@/components/common/Button";
import { Card } from "@/components/common/Card";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { RISK_PROFILES } from "@/lib/constants";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [settings, setSettings] = useState<Record<string, string>>({});
  const [loading, setLoading] = useState(true);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setSettings(await api.getSettings());
    } catch (err) {
      setError(err instanceof Error ? err.message : "설정을 불러오지 못했습니다.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void load();
  }, [load]);

  const save = async () => {
    setMessage("");
    setSettings(await api.updateSettings(settings));
    setMessage("설정을 저장했습니다.");
  };

  if (loading) return <LoadingSkeleton rows={3} />;
  if (error) return <ErrorState message={error} onRetry={load} />;

  return (
    <div className="space-y-4">
      <Card title="기본 설정">
        <div className="space-y-3">
          <Field label="기본 투자금">
            <input value={settings.defaultCapitalKRW ?? ""} onChange={(e) => setSettings({ ...settings, defaultCapitalKRW: e.target.value })} type="number" className="min-h-11 w-full rounded-[8px] bg-cardSoft px-3 font-bold outline-none" />
          </Field>
          <Field label="기본 리스크 성향">
            <select value={settings.defaultRiskProfile ?? "balanced"} onChange={(e) => setSettings({ ...settings, defaultRiskProfile: e.target.value })} className="min-h-11 w-full rounded-[8px] bg-cardSoft px-3 font-bold outline-none">
              {RISK_PROFILES.map((item) => (
                <option key={item.value} value={item.value}>{item.label} · {item.description}</option>
              ))}
            </select>
          </Field>
          <Field label="기본 환율 fallback">
            <input value={settings.defaultExchangeRate ?? ""} onChange={(e) => setSettings({ ...settings, defaultExchangeRate: e.target.value })} type="number" className="min-h-11 w-full rounded-[8px] bg-cardSoft px-3 font-bold outline-none" />
          </Field>
          <Field label="캐시 TTL(초)">
            <input value={settings.cacheTTLSeconds ?? ""} onChange={(e) => setSettings({ ...settings, cacheTTLSeconds: e.target.value })} type="number" className="min-h-11 w-full rounded-[8px] bg-cardSoft px-3 font-bold outline-none" />
          </Field>
        </div>
        <Button className="mt-4 w-full" onClick={save}>
          <Save className="h-4 w-4" />
          저장
        </Button>
        {message && <p className="mt-3 text-center text-xs font-bold text-primary">{message}</p>}
      </Card>
      <Card title="데이터 관리">
        <div className="grid gap-3">
          <Button
            variant="secondary"
            onClick={async () => {
              await api.clearCache();
              setMessage("캐시를 비웠습니다.");
            }}
          >
            <RefreshCw className="h-4 w-4" />
            데이터 새로고침
          </Button>
          <Button
            variant="danger"
            onClick={async () => {
              if (window.confirm("저장된 관심종목, 보유종목, 알림, 메모, 분석 스냅샷을 초기화할까요?")) {
                await api.resetDb();
                await load();
                setMessage("DB를 초기화했습니다.");
              }
            }}
          >
            <Trash2 className="h-4 w-4" />
            DB 초기화
          </Button>
        </div>
      </Card>
      <Card title="투자 유의사항">
        <div className="flex gap-3 rounded-[8px] bg-cardSoft p-4">
          <Database className="h-5 w-5 shrink-0 text-primary" />
          <p className="text-sm leading-6 text-subText">
            StoPro는 자동매매 앱이 아니며 주문 실행, 브로커 연동, 수익 보장을 제공하지 않습니다. 무료 데이터는 누락, 정정 가능성이 있어 실제 투자 전 공식 시세와 공시를 함께 확인해야 합니다.
          </p>
        </div>
      </Card>
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-bold text-subText">{label}</span>
      {children}
    </label>
  );
}
