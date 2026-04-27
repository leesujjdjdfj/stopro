"use client";

import { useEffect, useState } from "react";
import { Save } from "lucide-react";
import { Button } from "@/components/common/Button";
import { Card } from "@/components/common/Card";
import { api } from "@/lib/api";
import type { MemoItem } from "@/types/portfolio";

const fields = [
  { key: "thesis", label: "왜 보는 종목인지" },
  { key: "entry_condition", label: "진입 조건" },
  { key: "stop_condition", label: "손절 기준" },
  { key: "checklist", label: "확인할 이슈" },
  { key: "review", label: "내 판단" }
] as const;

export function MemoCard({ ticker }: { ticker: string }) {
  const [memo, setMemo] = useState<MemoItem>({ ticker });
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState("");

  useEffect(() => {
    api.getMemo(ticker).then(setMemo).catch(() => setMemo({ ticker }));
  }, [ticker]);

  const save = async () => {
    setSaving(true);
    setMessage("");
    try {
      await api.saveMemo({
        ticker,
        title: memo.title ?? "",
        thesis: memo.thesis ?? "",
        entryCondition: memo.entry_condition ?? "",
        stopCondition: memo.stop_condition ?? "",
        checklist: memo.checklist ?? "",
        review: memo.review ?? ""
      });
      setMessage("메모를 저장했습니다.");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "저장에 실패했습니다.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Card title="투자 메모">
      <input
        value={memo.title ?? ""}
        onChange={(event) => setMemo({ ...memo, title: event.target.value })}
        placeholder="메모 제목"
        className="mb-3 min-h-11 w-full rounded-[8px] bg-cardSoft px-3 text-sm font-bold outline-none"
      />
      <div className="space-y-3">
        {fields.map((field) => (
          <label key={field.key} className="block">
            <span className="mb-1 block text-xs font-bold text-subText">{field.label}</span>
            <textarea
              value={(memo[field.key] as string | null | undefined) ?? ""}
              onChange={(event) => setMemo({ ...memo, [field.key]: event.target.value })}
              rows={3}
              className="w-full resize-none rounded-[8px] bg-cardSoft p-3 text-sm leading-6 text-text outline-none"
            />
          </label>
        ))}
      </div>
      <Button className="mt-4 w-full" onClick={save} disabled={saving}>
        <Save className="h-4 w-4" />
        저장
      </Button>
      {message && <p className="mt-3 text-center text-xs font-bold text-subText">{message}</p>}
    </Card>
  );
}
