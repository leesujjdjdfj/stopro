import { Card } from "@/components/common/Card";
import { formatNumber } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function FundamentalCheckCard({ analysis }: { analysis: AnalysisResponse }) {
  const f = analysis.fundamentals;
  return (
    <Card title="기본적 지표">
      {!f.dataAvailable ? (
        <p className="text-sm leading-6 text-subText">기본적 지표 데이터가 부족합니다.</p>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          <Metric label="Market Cap" value={formatNumber(f.marketCap, 0)} />
          <Metric label="PER" value={formatNumber(f.trailingPE, 2)} />
          <Metric label="Forward PER" value={formatNumber(f.forwardPE, 2)} />
          <Metric label="EPS" value={formatNumber(f.eps, 2)} />
          <Metric label="Revenue Growth" value={f.revenueGrowth == null ? "-" : `${formatNumber(f.revenueGrowth * 100, 1)}%`} />
          <Metric label="Profit Margin" value={f.profitMargin == null ? "-" : `${formatNumber(f.profitMargin * 100, 1)}%`} />
          <Metric label="Debt to Equity" value={formatNumber(f.debtToEquity, 1)} />
        </div>
      )}
      <div className="mt-4 space-y-2">
        {f.notes.map((note) => (
          <p key={note} className="rounded-[8px] bg-cardSoft p-3 text-xs leading-5 text-subText">{note}</p>
        ))}
      </div>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className="mt-1 text-sm font-black text-text">{value}</p>
    </div>
  );
}
