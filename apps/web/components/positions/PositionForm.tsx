"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/common/Button";

export function PositionForm({
  onAdd,
  loading
}: {
  onAdd: (payload: { ticker: string; averagePrice: number; quantity: number; targetPrice?: number; stopLoss?: number; note?: string }) => Promise<void>;
  loading?: boolean;
}) {
  const [ticker, setTicker] = useState("");
  const [averagePrice, setAveragePrice] = useState("");
  const [quantity, setQuantity] = useState("");
  const [targetPrice, setTargetPrice] = useState("");
  const [stopLoss, setStopLoss] = useState("");
  const [note, setNote] = useState("");

  const submit = async () => {
    await onAdd({
      ticker,
      averagePrice: Number(averagePrice),
      quantity: Number(quantity),
      targetPrice: targetPrice ? Number(targetPrice) : undefined,
      stopLoss: stopLoss ? Number(stopLoss) : undefined,
      note
    });
    setTicker("");
    setAveragePrice("");
    setQuantity("");
    setTargetPrice("");
    setStopLoss("");
    setNote("");
  };

  return (
    <div className="rounded-[8px] border border-border bg-white p-4 shadow-soft">
      <div className="grid grid-cols-2 gap-3">
        <Input label="티커" value={ticker} onChange={(v) => setTicker(v.toUpperCase())} placeholder="NVDA" />
        <Input label="수량" value={quantity} onChange={setQuantity} type="number" placeholder="10" />
        <Input label="평균 매수가" value={averagePrice} onChange={setAveragePrice} type="number" placeholder="120" />
        <Input label="목표가" value={targetPrice} onChange={setTargetPrice} type="number" placeholder="135" />
        <Input label="손절가" value={stopLoss} onChange={setStopLoss} type="number" placeholder="112" />
        <Input label="메모" value={note} onChange={setNote} placeholder="매수 이유" />
      </div>
      <Button className="mt-4 w-full" onClick={submit} disabled={!ticker || !averagePrice || !quantity || loading}>
        <Plus className="h-4 w-4" />
        보유 종목 저장
      </Button>
    </div>
  );
}

function Input({
  label,
  value,
  onChange,
  placeholder,
  type = "text"
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="mb-1 block text-xs font-bold text-subText">{label}</span>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        type={type}
        className="min-h-11 w-full rounded-[8px] bg-cardSoft px-3 text-sm font-bold outline-none"
      />
    </label>
  );
}
