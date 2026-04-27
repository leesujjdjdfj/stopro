"use client";

import { useMemo, useState } from "react";
import { Bar, CartesianGrid, ComposedChart, Legend, Line, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Card } from "@/components/common/Card";
import type { AnalysisResponse } from "@/types/analysis";

const periods = [
  { label: "1M", days: 23 },
  { label: "3M", days: 69 },
  { label: "6M", days: 138 },
  { label: "1Y", days: 252 },
  { label: "2Y", days: 504 }
];

export function PriceChartCard({ analysis }: { analysis: AnalysisResponse }) {
  const [period, setPeriod] = useState(periods[3]);
  const data = useMemo(() => analysis.chart.slice(-period.days), [analysis.chart, period.days]);
  return (
    <Card
      title="가격 차트"
      action={
        <div className="flex rounded-[8px] bg-cardSoft p-1">
          {periods.map((item) => (
            <button
              key={item.label}
              onClick={() => setPeriod(item)}
              className={`h-8 rounded-[6px] px-2 text-[11px] font-black ${period.label === item.label ? "bg-white text-primary shadow-sm" : "text-subText"}`}
            >
              {item.label}
            </button>
          ))}
        </div>
      }
    >
      <div className="h-[310px] w-full">
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data} margin={{ top: 10, right: 0, bottom: 0, left: -22 }}>
            <CartesianGrid stroke="#E5E7EB" vertical={false} />
            <XAxis dataKey="date" tick={{ fontSize: 10, fill: "#6B7280" }} tickLine={false} axisLine={false} minTickGap={26} />
            <YAxis yAxisId="price" tick={{ fontSize: 10, fill: "#6B7280" }} tickLine={false} axisLine={false} domain={["auto", "auto"]} />
            <YAxis yAxisId="volume" hide />
            <Tooltip contentStyle={{ borderRadius: 8, border: "1px solid #E5E7EB" }} />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Bar yAxisId="volume" dataKey="volume" fill="#E5E7EB" barSize={8} name="거래량" />
            <Line yAxisId="price" type="monotone" dataKey="close" stroke="#111827" strokeWidth={2} dot={false} name="종가" />
            <Line yAxisId="price" type="monotone" dataKey="ma20" stroke="#4F7CFF" strokeWidth={1.5} dot={false} name="MA20" />
            <Line yAxisId="price" type="monotone" dataKey="ma60" stroke="#FF6A1A" strokeWidth={1.5} dot={false} name="MA60" />
            <Line yAxisId="price" type="monotone" dataKey="ma200" stroke="#22C55E" strokeWidth={1.5} dot={false} name="MA200" />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </Card>
  );
}
