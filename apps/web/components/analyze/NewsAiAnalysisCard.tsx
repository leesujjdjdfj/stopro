"use client";

import { AlertCircle, ExternalLink, Newspaper, Sparkles } from "lucide-react";
import { useEffect, useState } from "react";
import { Card } from "@/components/common/Card";
import { LoadingSkeleton } from "@/components/common/LoadingSkeleton";
import { api } from "@/lib/api";
import { formatNumber } from "@/lib/format";
import type { AnalysisResponse, NewsAnalysisResponse, NewsSentiment } from "@/types/analysis";

export function NewsAiAnalysisCard({ analysis }: { analysis: AnalysisResponse }) {
  const [data, setData] = useState<NewsAnalysisResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    setLoading(true);
    setError("");
    api
      .analyzeNews({
        ticker: analysis.displayTicker || analysis.ticker,
        companyName: analysis.name,
        currentPrice: analysis.currentPrice,
        dailyChangePercent: analysis.dailyChangePercent,
        technicalContext: {
          currentPrice: analysis.currentPrice,
          dailyChangePercent: analysis.dailyChangePercent,
          ma20: analysis.indicators.ma20,
          ma60: analysis.indicators.ma60,
          ma200: analysis.indicators.ma200,
          rsi: analysis.indicators.rsi,
          rewardRiskRatio: analysis.rewardRisk.ratioToSecondTarget,
          riskScore: analysis.risk.score,
          supportPrice: analysis.supportResistance?.support?.price,
          resistancePrice: analysis.supportResistance?.resistance?.price
        }
      })
      .then((result) => {
        if (!alive) return;
        setData(result);
      })
      .catch((err) => {
        if (!alive) return;
        setError(err instanceof Error ? err.message : "뉴스 기반 AI 분석을 불러오지 못했습니다.");
      })
      .finally(() => {
        if (alive) setLoading(false);
      });

    return () => {
      alive = false;
    };
  }, [analysis.currentPrice, analysis.dailyChangePercent, analysis.displayTicker, analysis.name, analysis.ticker]);

  if (loading) {
    return (
      <Card title="뉴스 기반 AI 분석">
        <LoadingSkeleton rows={5} />
      </Card>
    );
  }

  if (error) {
    return (
      <Card title="뉴스 기반 AI 분석">
        <div className="rounded-[8px] border border-warning/20 bg-warning/10 p-4 text-sm leading-6 text-text">
          <div className="flex items-start gap-2">
            <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-warning" />
            <div>
              <p className="font-black">뉴스 분석을 표시하지 못했습니다.</p>
              <p className="mt-1 text-subText">{error}</p>
            </div>
          </div>
        </div>
      </Card>
    );
  }

  if (!data) return null;

  const tone = sentimentTone(data.sentiment);
  const sentimentLabel = sentimentText(data.sentiment);

  return (
    <Card>
      <div className="mb-4 flex items-start justify-between gap-3">
        <div>
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-[8px] bg-primary/10 text-primary">
              <Sparkles className="h-4 w-4" />
            </span>
            <div>
              <h2 className="text-base font-black text-text">뉴스 기반 AI 분석</h2>
              <p className="mt-0.5 text-[11px] font-bold text-subText">
                뉴스 + AI 종합 해석 · {data.newsSource} · {data.aiProvider}
                {data.cacheHit ? " · 캐시" : ""}
              </p>
            </div>
          </div>
        </div>
        <span className={`rounded-full px-3 py-1 text-xs font-black ${tone.badge}`}>{sentimentLabel}</span>
      </div>

      <div className={`rounded-[8px] p-4 ${tone.panel}`}>
        <p className="text-xs font-black opacity-70">감정 점수</p>
        <p className={`mt-1 text-3xl font-black ${tone.text}`}>{signedScore(data.sentimentScore)}</p>
        <p className="mt-3 text-sm font-black leading-6 text-text">{data.oneLine}</p>
      </div>

      <p className="mt-4 text-sm leading-6 text-text">{data.summary}</p>
      {data.technicalVsNews ? (
        <p className="mt-3 rounded-[8px] bg-cardSoft p-3 text-xs font-bold leading-5 text-subText">
          차트와 뉴스 방향성: {alignmentLabel(data.technicalVsNews)}
        </p>
      ) : null}

      <div className="mt-4 grid grid-cols-1 gap-2.5">
        <Section title="핵심 이슈" items={data.keyIssues} />
        <Section title="긍정 요인" items={data.positiveFactors} tone="red" />
        <Section title="부정 요인" items={data.negativeFactors} tone="blue" />
        <Section title="리스크 요인" items={data.riskFactors} tone="warning" />
        <Section title="확인할 포인트" items={data.watchPoints} />
      </div>

      <div className="mt-4 rounded-[8px] border border-border bg-cardSoft p-3">
        <div className="mb-3 flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Newspaper className="h-4 w-4 text-primary" />
            <h3 className="text-sm font-black text-text">최근 뉴스</h3>
          </div>
          <span className="text-[11px] font-bold text-subText">신뢰도 {confidenceLabel(data.confidence)}</span>
        </div>
        {data.newsItems.length ? (
          <div className="space-y-3">
            {data.newsItems.slice(0, 5).map((item) => (
              <a
                key={`${item.url}-${item.title}`}
                href={item.url}
                target="_blank"
                rel="noreferrer"
              className="block rounded-[8px] bg-white p-3 active:bg-gray-50"
              >
                <div className="flex items-start justify-between gap-3">
                  <p className="text-sm font-black leading-5 text-text">{item.title}</p>
                  <ExternalLink className="mt-0.5 h-4 w-4 shrink-0 text-subText" />
                </div>
                <p className="mt-2 text-xs font-bold text-subText">
                  {item.source || "Unknown"} · {formatNewsDate(item.publishedAt)}
                </p>
              </a>
            ))}
          </div>
        ) : (
          <p className="rounded-[8px] bg-white p-3 text-sm font-bold text-subText">최근 뉴스가 충분하지 않습니다.</p>
        )}
      </div>

      <div className="mt-4 space-y-1 text-[11px] leading-5 text-subText">
        <p>뉴스 데이터는 외부 무료 API 기반이며 누락되거나 지연될 수 있습니다.</p>
        <p>AI 분석은 기사 제목과 요약을 기반으로 생성된 참고용 해석입니다.</p>
        <p className="font-bold text-text">{data.disclaimer}</p>
      </div>
    </Card>
  );
}

function Section({ title, items, tone = "gray" }: { title: string; items: string[]; tone?: "gray" | "red" | "blue" | "warning" }) {
  const titleClass = {
    gray: "text-text",
    red: "text-up",
    blue: "text-down",
    warning: "text-warning"
  }[tone];

  return (
    <div className={`rounded-[8px] border p-3 ${tone === "warning" ? "border-warning/20 bg-warning/10" : "border-border bg-white"}`}>
      <h3 className={`text-sm font-black ${titleClass}`}>{title}</h3>
      <ul className="mt-2 space-y-2">
        {(items.length ? items : ["추가 확인이 필요합니다."]).map((item) => (
          <li key={item} className="flex gap-2 text-sm leading-6 text-text">
            <span className="mt-2 h-1.5 w-1.5 shrink-0 rounded-full bg-primary/50" />
            <span>{item}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

function sentimentTone(sentiment: NewsSentiment) {
  if (sentiment === "positive") {
    return { text: "text-up", badge: "bg-red-50 text-up", panel: "bg-red-50" };
  }
  if (sentiment === "negative") {
    return { text: "text-down", badge: "bg-blue-50 text-down", panel: "bg-blue-50" };
  }
  if (sentiment === "neutral") {
    return { text: "text-subText", badge: "bg-cardSoft text-subText", panel: "bg-cardSoft" };
  }
  return { text: "text-warning", badge: "bg-warning/10 text-warning", panel: "bg-warning/10" };
}

function sentimentText(sentiment: NewsSentiment) {
  const labels: Record<NewsSentiment, string> = {
    positive: "긍정",
    neutral: "중립",
    negative: "부정",
    mixed: "혼재"
  };
  return labels[sentiment];
}

function confidenceLabel(value: "high" | "medium" | "low") {
  const labels = { high: "높음", medium: "보통", low: "낮음" };
  return labels[value];
}

function alignmentLabel(value: "aligned" | "diverged" | "mixed" | "insufficient") {
  return { aligned: "일치", diverged: "엇갈림", mixed: "혼재", insufficient: "판단 부족" }[value];
}

function signedScore(value: number) {
  const sign = value > 0 ? "+" : "";
  return `${sign}${formatNumber(value, 0)}`;
}

function formatNewsDate(value?: string | null) {
  if (!value) return "날짜 없음";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("ko-KR", { month: "short", day: "numeric" }).format(date);
}
