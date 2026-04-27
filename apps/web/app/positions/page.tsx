"use client";

import { useCallback, useEffect, useState } from "react";
import { EmptyState } from "@/components/common/EmptyState";
import { ErrorState } from "@/components/common/ErrorState";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { PositionForm } from "@/components/positions/PositionForm";
import { PositionRiskCard } from "@/components/positions/PositionRiskCard";
import { PositionTable } from "@/components/positions/PositionTable";
import { api } from "@/lib/api";
import type { PositionItem } from "@/types/portfolio";

export default function PositionsPage() {
  const [positions, setPositions] = useState<PositionItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      setPositions(await api.getPositions());
    } catch (err) {
      setError(err instanceof Error ? err.message : "보유 종목을 불러오지 못했습니다.");
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
      <PositionForm
        loading={saving}
        onAdd={async (payload) => {
          setSaving(true);
          await api.addPosition(payload);
          setSaving(false);
          await load();
        }}
      />
      {positions.length === 0 ? (
        <EmptyState title="보유 종목이 없습니다" description="계좌 연동 없이 직접 평균가, 수량, 목표가, 손절가를 저장해 리스크를 관리합니다." />
      ) : (
        <>
          <PositionRiskCard positions={positions} />
          <PositionTable
            positions={positions}
            onDelete={async (id) => {
              await api.deletePosition(id);
              await load();
            }}
          />
        </>
      )}
    </div>
  );
}
