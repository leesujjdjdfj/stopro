"use client";

import { useState } from "react";
import { BellPlus } from "lucide-react";
import { Button } from "@/components/common/Button";

const conditions = [
  { value: "above", label: "현재가 이상" },
  { value: "below", label: "현재가 이하" },
  { value: "target_reached", label: "목표가 도달" },
  { value: "stop_near", label: "손절가 근접" }
];

export function AlertForm({
  onAdd,
  loading
}: {
  onAdd: (payload: { ticker: string; conditionType: string; targetPrice: number; message?: string; isActive: boolean }) => Promise<void>;
  loading?: boolean;
}) {
  const [ticker, setTicker] = useState("");
  const [conditionType, setConditionType] = useState("above");
  const [targetPrice, setTargetPrice] = useState("");
  const [message, setMessage] = useState("");

  const submit = async () => {
    await onAdd({ ticker, conditionType, targetPrice: Number(targetPrice), message, isActive: true });
    setTicker("");
    setTargetPrice("");
    setMessage("");
  };

  return (
    <div className="rounded-[8px] border border-border bg-white p-4 shadow-soft">
      <div className="grid grid-cols-2 gap-3">
        <input value={ticker} onChange={(e) => setTicker(e.target.value.toUpperCase())} placeholder="티커" className="min-h-11 rounded-[8px] bg-cardSoft px-3 text-sm font-bold outline-none" />
        <select value={conditionType} onChange={(e) => setConditionType(e.target.value)} className="min-h-11 rounded-[8px] bg-cardSoft px-3 text-sm font-bold outline-none">
          {conditions.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}
        </select>
        <input value={targetPrice} onChange={(e) => setTargetPrice(e.target.value)} type="number" placeholder="기준 가격" className="min-h-11 rounded-[8px] bg-cardSoft px-3 text-sm font-bold outline-none" />
        <input value={message} onChange={(e) => setMessage(e.target.value)} placeholder="메시지" className="min-h-11 rounded-[8px] bg-cardSoft px-3 text-sm font-bold outline-none" />
      </div>
      <Button className="mt-4 w-full" onClick={submit} disabled={!ticker || !targetPrice || loading}>
        <BellPlus className="h-4 w-4" />
        알림 조건 저장
      </Button>
    </div>
  );
}
