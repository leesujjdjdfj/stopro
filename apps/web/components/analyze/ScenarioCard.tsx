import { Card } from "@/components/common/Card";
import { formatPrice } from "@/lib/format";
import type { AnalysisResponse } from "@/types/analysis";

export function ScenarioCard({ analysis }: { analysis: AnalysisResponse }) {
  return (
    <Card title="시나리오">
      <div className="space-y-3">
        {analysis.scenarios.map((scenario) => (
          <div key={scenario.name} className="rounded-[8px] border border-border p-4">
            <div className="flex items-center justify-between gap-3">
              <p className="font-black text-text">{scenario.name}</p>
              <p className="text-lg font-black text-primary">{scenario.probability}%</p>
            </div>
            <p className="mt-2 text-sm leading-6 text-subText">조건: {scenario.condition}</p>
            <p className="mt-1 text-sm leading-6 text-subText">대응: {scenario.response}</p>
            <p className="mt-2 text-xs font-bold text-text">확인 가격 {formatPrice(scenario.checkPrice, analysis.currency)}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
