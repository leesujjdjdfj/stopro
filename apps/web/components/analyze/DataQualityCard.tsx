import { Database } from "lucide-react";
import { Card } from "@/components/common/Card";
import { Badge } from "@/components/common/Badge";
import { formatDateTime } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function DataQualityCard({ analysis }: { analysis: AnalysisResponse }) {
  const q = analysis.dataQuality;
  const tone = q.status === "good" ? "green" : q.status === "partial" ? "orange" : "red";
  return (
    <Card title="데이터 품질">
      <div className="flex items-start gap-3">
        <Database className="mt-1 h-5 w-5 text-primary" />
        <div>
          <Badge tone={tone}>{q.status}</Badge>
          <p className="mt-3 text-sm leading-6 text-subText">{q.message}</p>
        </div>
      </div>
      <div className="mt-4 grid grid-cols-2 gap-3">
        <Metric label="데이터 소스" value={q.source} />
        <Metric label="마지막 업데이트" value={formatDateTime(q.lastUpdated)} />
        <Metric label="캐시 여부" value={q.cacheHit ? "캐시 사용" : "신규 조회"} />
        <Metric label="결측 종가" value={`${q.missingRows}개`} />
        <Metric label="분석 가능" value={q.analysisAvailable ? "가능" : "제한"} />
      </div>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className="mt-1 break-words text-sm font-black text-text">{value}</p>
    </div>
  );
}
