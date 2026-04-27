"use client";

import { QUICK_CAPITALS, RISK_PROFILES } from "@/lib/constants";
import { formatKRW } from "@/lib/format";

export function CapitalInput({
  capital,
  riskProfile,
  onCapitalChange,
  onRiskProfileChange
}: {
  capital: number;
  riskProfile: string;
  onCapitalChange: (value: number) => void;
  onRiskProfileChange: (value: string) => void;
}) {
  return (
    <div className="rounded-[8px] border border-border bg-white p-4 shadow-soft">
      <label className="text-xs font-bold text-subText">투자금</label>
      <input
        value={capital}
        type="number"
        min={0}
        onChange={(event) => onCapitalChange(Number(event.target.value))}
        className="mt-1 min-h-12 w-full rounded-[8px] bg-cardSoft px-3 text-xl font-black text-text outline-none"
      />
      <p className="mt-1 text-xs font-bold text-primary">{formatKRW(capital)}</p>
      <div className="mt-3 grid grid-cols-3 gap-2">
        {QUICK_CAPITALS.map((item) => (
          <button
            key={item.value}
            type="button"
            onClick={() => onCapitalChange(item.value)}
            className="min-h-10 rounded-[8px] bg-cardSoft text-xs font-bold text-text active:bg-border"
          >
            {item.label}
          </button>
        ))}
      </div>
      <div className="mt-4 grid grid-cols-3 gap-2">
        {RISK_PROFILES.map((item) => (
          <button
            key={item.value}
            type="button"
            onClick={() => onRiskProfileChange(item.value)}
            className={`min-h-12 rounded-[8px] border px-2 text-xs font-bold ${
              riskProfile === item.value ? "border-primary bg-primary text-white" : "border-border bg-white text-text"
            }`}
          >
            {item.label}
            <span className="block text-[10px] opacity-80">{item.description}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
