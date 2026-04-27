"use client";

import { useState } from "react";
import { Plus } from "lucide-react";
import { Button } from "@/components/common/Button";

export function WatchlistForm({ onAdd, loading }: { onAdd: (ticker: string, note?: string) => Promise<void>; loading?: boolean }) {
  const [ticker, setTicker] = useState("");
  const [note, setNote] = useState("");
  return (
    <div className="rounded-[8px] border border-border bg-white p-4 shadow-soft">
      <div className="grid gap-3">
        <input
          value={ticker}
          onChange={(event) => setTicker(event.target.value.toUpperCase())}
          placeholder="티커 추가: NVDA"
          className="min-h-12 rounded-[8px] bg-cardSoft px-3 text-base font-black outline-none"
        />
        <input
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="관심 사유 메모"
          className="min-h-11 rounded-[8px] bg-cardSoft px-3 text-sm outline-none"
        />
        <Button
          disabled={!ticker.trim() || loading}
          onClick={async () => {
            await onAdd(ticker, note);
            setTicker("");
            setNote("");
          }}
        >
          <Plus className="h-4 w-4" />
          관심종목 추가
        </Button>
      </div>
    </div>
  );
}
