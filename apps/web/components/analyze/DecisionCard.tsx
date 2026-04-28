"use client";

import { AlertTriangle, CheckCircle2, ChevronDown, CircleDashed, OctagonAlert, PauseCircle, XCircle } from "lucide-react";
import { useState } from "react";
import { Card } from "@/components/common/Card";
import { StockIdentity } from "@/components/common/StockIdentity";
import { formatPercent, formatPrice } from "@/lib/format";
import type { AnalysisResponse, InsightBreakdown, InsightDetail, InvestmentInsight } from "@/types/analysis";

const iconMap = {
  candidate: CheckCircle2,
  split_buy: CircleDashed,
  watch: PauseCircle,
  caution: OctagonAlert,
  avoid: OctagonAlert
};

export function DecisionCard({ analysis }: { analysis: AnalysisResponse }) {
  const insight = analysis.investmentInsight;
  const Icon = iconMap[analysis.decision.status];
  const isRisk = analysis.decision.status === "caution" || analysis.decision.status === "avoid";
  const suitability = analysis.decision.buySuitability;
  const percent = insight?.score ?? suitability?.percent ?? analysis.decision.buySuitabilityPercent ?? analysis.decision.score;
  const label = insight?.finalLabel ?? analysis.decision.label;
  const tone = insight ? toneClass(insight.tone) : isRisk ? "text-danger" : "text-primary";

  return (
    <Card>
      <StockIdentity stock={analysis} className="mb-4" nameClassName="text-lg font-black text-text" />
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs font-bold text-subText">투자 판단 보조</p>
          <p className={`mt-1 text-3xl font-black ${tone}`}>{label}</p>
          {insight ? (
            <p className="mt-2 text-xs font-bold text-subText">
              기술 {insight.technicalScore}점 · 뉴스 {signedScore(insight.newsScore)}점 · 신뢰도 {confidenceLabel(insight.confidence)}
            </p>
          ) : null}
        </div>
        <Icon className={`h-9 w-9 ${tone}`} />
      </div>

      <div className="mt-5 rounded-[8px] bg-cardSoft p-4">
        <div className="flex items-end justify-between gap-3">
          <div>
            <p className="text-xs font-bold text-subText">분석상 매수 적합도</p>
            <p className={`mt-1 text-4xl font-black ${suitabilityTone(percent)}`}>{percent}%</p>
          </div>
          <p className="rounded-full bg-white px-3 py-1 text-xs font-black text-subText">
            {insight ? insightBadge(percent) : suitability?.label ?? "조건 점수"}
          </p>
        </div>
        <div className="mt-3 h-2 overflow-hidden rounded-full bg-border">
          <div className={`h-full rounded-full ${suitabilityBar(percent)}`} style={{ width: `${Math.max(0, Math.min(100, percent))}%` }} />
        </div>
        {insight ? <InsightScoreBars insight={insight} /> : <LegacyFactorBars factors={suitability?.factors} />}
        <p className="mt-3 text-xs leading-5 text-subText">
          {insight ? "이 수치는 매수 권유나 수익 확률이 아니라 현재 지표와 뉴스 조건 충족도를 0~100으로 환산한 값입니다." : suitability?.description ?? "현재 지표 조건을 0~100으로 환산한 참고 점수입니다."}
        </p>
      </div>

      {insight ? <InvestmentInsightBody insight={insight} analysis={analysis} /> : <LegacyBody analysis={analysis} />}
    </Card>
  );
}

function InvestmentInsightBody({ insight, analysis }: { insight: InvestmentInsight; analysis: AnalysisResponse }) {
  const newsChart = insight.newsChartAlignment ?? insight.technicalVsNews;
  return (
    <div className="mt-4 space-y-4">
      <section className="rounded-[8px] border border-primary/15 bg-blue-50 p-4">
        <p className="text-xs font-black text-primary">핵심 요약</p>
        <p className="mt-2 text-[15px] font-semibold leading-7 text-text">{insight.oneLine}</p>
        <p className="mt-3 text-sm leading-6 text-subText">{insight.summary}</p>
      </section>

      <section className="space-y-2">
        {insight.scoreBreakdown.map((item) => (
          <BreakdownAccordion key={item.key} item={item} />
        ))}
      </section>

      <div className="grid grid-cols-1 gap-3">
        <PointList title="긍정 요인" items={insight.positivePoints} tone="positive" />
        <PointList title="부정 요인" items={insight.negativePoints} tone="negative" />
        <PointList title="확인해야 할 조건" items={insight.watchPoints} tone="watch" />
      </div>

      <section className="rounded-[8px] border border-border bg-white p-4">
        <h3 className="text-sm font-black text-text">리스크 관리 기준</h3>
        <div className="mt-3 grid grid-cols-2 gap-2">
          <Metric label="지지선" value={formatPrice(insight.riskManagement.supportPrice, analysis.currency)} sub={formatPercent(insight.riskManagement.supportDistancePercent)} />
          <Metric label="저항선" value={formatPrice(insight.riskManagement.resistancePrice, analysis.currency)} sub={formatPercent(insight.riskManagement.resistanceDistancePercent)} />
          <Metric label="손절 참고" value={formatPrice(insight.riskManagement.stopLossGuide, analysis.currency)} />
          <Metric label="뉴스/차트" value={newsChart.label ?? alignmentLabel(newsChart.alignment)} />
        </div>
        <div className={`mt-3 rounded-[8px] border p-3 ${alignmentTone(newsChart.alignment)}`}>
          <p className="text-xs font-black">뉴스-차트 일치도 · {newsChart.label ?? alignmentLabel(newsChart.alignment)}</p>
          <p className="mt-2 text-sm font-black leading-6 text-text">{newsChart.message ?? alignmentMessage(newsChart.alignment)}</p>
          <p className="mt-1 text-xs leading-5 text-subText">{newsChart.summary}</p>
        </div>
        <p className="mt-3 rounded-[8px] bg-cardSoft p-3 text-xs leading-5 text-subText">{insight.riskManagement.invalidationCondition}</p>
      </section>

      <p className="rounded-[8px] bg-cardSoft p-3 text-xs leading-5 text-subText">
        이 수치는 매수 권유나 수익 확률이 아니라 현재 지표와 뉴스 조건 충족도를 0~100으로 환산한 값입니다. {insight.disclaimer}
      </p>
    </div>
  );
}

function BreakdownAccordion({ item }: { item: InsightBreakdown }) {
  const [open, setOpen] = useState(false);
  const ratio = item.key === "news" ? Math.min(100, Math.abs((item.score / item.maxScore) * 100)) : Math.round((item.score / item.maxScore) * 100);
  const isNegativeNews = item.key === "news" && item.score < 0;

  return (
    <div className="rounded-[8px] border border-border bg-white">
      <button type="button" onClick={() => setOpen((value) => !value)} className="flex w-full items-center justify-between gap-3 p-4 text-left">
        <div className="min-w-0 flex-1">
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-black text-text">{item.name}</p>
            <p className="text-xs font-black text-subText">
              {item.key === "news" ? signedScore(item.score) : item.score}/{item.maxScore}
            </p>
          </div>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-cardSoft">
            <div className={`h-full rounded-full ${isNegativeNews ? "bg-down" : item.score >= item.maxScore * 0.6 ? "bg-primary" : "bg-warning"}`} style={{ width: `${Math.max(0, Math.min(100, ratio))}%` }} />
          </div>
          <p className="mt-2 line-clamp-2 text-xs leading-5 text-subText">{item.summary}</p>
        </div>
        <ChevronDown className={`h-4 w-4 shrink-0 text-subText transition ${open ? "rotate-180" : ""}`} />
      </button>
      {open ? (
        <div className="border-t border-border px-4 pb-4 pt-2">
          <p className="mb-2 text-xs font-black text-primary">{item.label}</p>
          <div className="space-y-2">
            {(item.details ?? []).map((detail) => (
              <ConditionRow key={`${item.key}-${detail.condition}-${detail.value}`} detail={detail} />
            ))}
          </div>
        </div>
      ) : null}
    </div>
  );
}

function ConditionRow({ detail }: { detail: InsightDetail }) {
  const Icon = detail.passed ? CheckCircle2 : XCircle;
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <div className="flex items-start gap-2">
        <Icon className={`mt-0.5 h-4 w-4 shrink-0 ${detail.passed ? "text-safe" : "text-subText"}`} />
        <div className="min-w-0">
          <p className="text-xs font-black text-text">{detail.condition}</p>
          <p className="mt-1 text-xs font-bold text-subText">{detail.value}</p>
          <p className="mt-1 text-xs leading-5 text-subText">{detail.impact}</p>
        </div>
      </div>
    </div>
  );
}

function InsightScoreBars({ insight }: { insight: InvestmentInsight }) {
  return (
    <div className="mt-4 grid grid-cols-3 gap-1.5">
      {insight.scoreBreakdown.map((factor) => (
        <div key={factor.key} className="min-w-0">
          <div className="h-1.5 overflow-hidden rounded-full bg-white">
            <div className={`h-full rounded-full ${factor.key === "news" && factor.score < 0 ? "bg-down" : "bg-primary"}`} style={{ width: `${Math.min(100, Math.abs((factor.score / factor.maxScore) * 100))}%` }} />
          </div>
          <p className="mt-1 truncate text-[10px] font-bold text-subText">{factor.name}</p>
        </div>
      ))}
    </div>
  );
}

function LegacyFactorBars({ factors }: { factors?: { name: string; score: number; maxScore: number }[] }) {
  if (!factors?.length) return null;
  return (
    <div className="mt-4 grid grid-cols-5 gap-1.5">
      {factors.map((factor) => (
        <div key={factor.name} className="min-w-0">
          <div className="h-1.5 overflow-hidden rounded-full bg-white">
            <div className="h-full rounded-full bg-primary" style={{ width: `${Math.round((factor.score / factor.maxScore) * 100)}%` }} />
          </div>
          <p className="mt-1 truncate text-[10px] font-bold text-subText">{factor.name}</p>
        </div>
      ))}
    </div>
  );
}

function PointList({ title, items, tone }: { title: string; items: string[]; tone: "positive" | "negative" | "watch" }) {
  const styles = {
    positive: "border-red-100 bg-red-50 text-up",
    negative: "border-blue-100 bg-blue-50 text-down",
    watch: "border-warning/20 bg-warning/10 text-warning"
  };
  return (
    <section className={`rounded-[8px] border p-4 ${styles[tone]}`}>
      <h3 className="text-sm font-black">{title}</h3>
      <ul className="mt-2 space-y-2">
        {items.map((item) => (
          <li key={item} className="flex gap-2 text-sm leading-6 text-text">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-current opacity-60" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </section>
  );
}

function Metric({ label, value, sub }: { label: string; value: string; sub?: string }) {
  return (
    <div className="rounded-[8px] bg-cardSoft p-3">
      <p className="text-[11px] font-bold text-subText">{label}</p>
      <p className="mt-1 text-sm font-black text-text">{value}</p>
      {sub ? <p className="mt-1 text-[11px] font-bold text-subText">{sub}</p> : null}
    </div>
  );
}

function LegacyBody({ analysis }: { analysis: AnalysisResponse }) {
  const suitability = analysis.decision.buySuitability;
  return (
    <>
      <p className="mt-4 text-sm leading-6 text-subText">{analysis.decision.reason}</p>
      <p className="mt-3 rounded-[8px] bg-cardSoft p-3 text-xs leading-5 text-subText">
        {suitability?.note ?? "“매수 후보”는 매수 권유가 아니라 분석상 조건이 상대적으로 양호하다는 뜻입니다."}
      </p>
    </>
  );
}

function suitabilityTone(percent: number) {
  if (percent >= 75) return "text-safe";
  if (percent >= 60) return "text-primary";
  if (percent >= 45) return "text-warning";
  return "text-danger";
}

function suitabilityBar(percent: number) {
  if (percent >= 75) return "bg-safe";
  if (percent >= 60) return "bg-primary";
  if (percent >= 45) return "bg-warning";
  return "bg-danger";
}

function insightBadge(percent: number) {
  if (percent >= 75) return "양호";
  if (percent >= 60) return "보통 이상";
  if (percent >= 45) return "중립";
  if (percent >= 25) return "주의";
  return "회피";
}

function toneClass(tone: InvestmentInsight["tone"]) {
  const classes = {
    positive: "text-safe",
    cautious: "text-primary",
    neutral: "text-warning",
    warning: "text-danger",
    danger: "text-danger"
  };
  return classes[tone];
}

function signedScore(value: number) {
  return `${value > 0 ? "+" : ""}${value}`;
}

function confidenceLabel(value: "high" | "medium" | "low") {
  return { high: "높음", medium: "보통", low: "낮음" }[value];
}

function alignmentLabel(value: InvestmentInsight["technicalVsNews"]["alignment"]) {
  return { aligned: "일치", diverged: "엇갈림", mixed: "혼재", insufficient: "부족" }[value];
}

function alignmentMessage(value: InvestmentInsight["technicalVsNews"]["alignment"]) {
  return {
    aligned: "뉴스와 차트가 같은 방향입니다",
    diverged: "뉴스와 차트 신호가 엇갈려 추가 확인이 필요합니다",
    mixed: "뉴스와 차트 신호가 혼재되어 있습니다",
    insufficient: "뉴스와 차트 방향성을 판단하기에는 데이터가 부족합니다"
  }[value];
}

function alignmentTone(value: InvestmentInsight["technicalVsNews"]["alignment"]) {
  return {
    aligned: "border-safe/20 bg-safe/10",
    diverged: "border-warning/30 bg-warning/10",
    mixed: "border-border bg-cardSoft",
    insufficient: "border-border bg-cardSoft"
  }[value];
}
