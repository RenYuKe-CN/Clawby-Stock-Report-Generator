"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Area, AreaChart,
} from "recharts";
import { Loader2 } from "lucide-react";

interface Props {
  ticker: string;
}

interface MentionPoint {
  date: string;
  count: number;
}

export default function GaugeSentiment({ ticker }: Props) {
  const [data, setData] = useState<MentionPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/sentiment/${ticker}`)
      .then((r) => r.json())
      .then((res) => {
        const daily = (res.daily_counts || []) as Array<Record<string, unknown>>;
        const parsed: MentionPoint[] = daily
          .map((d) => ({
            date: String(d.date || "").slice(0, 10),
            count: Number(d.count || d.mention_count || 0),
          }))
          .sort((a, b) => a.date.localeCompare(b.date))
          .slice(-30);
        setData(parsed);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [ticker]);

  if (loading) {
    return <div className="skeleton" style={{ height: 200 }} />;
  }
  if (data.length === 0) {
    return <div className="text-xs text-[#4a5568] text-center py-8">暂无情绪数据</div>;
  }

  const total = data.reduce((s, d) => s + d.count, 0);
  const avg = Math.round(total / data.length);

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-[#7c8db5]">Reddit 讨论热度 · 近 {data.length} 天</span>
        <span className="text-xs text-[#e2e8f0] font-mono">日均 {avg} 次提及</span>
      </div>
      <ResponsiveContainer width="100%" height={200}>
        <AreaChart data={data}>
          <defs>
            <linearGradient id="sentimentGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.3} />
              <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" tick={{ fill: "#4a5568", fontSize: 10 }} tickLine={false} />
          <YAxis tick={{ fill: "#4a5568", fontSize: 10 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1a1d2e", border: "1px solid #2d3748", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Area type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} fill="url(#sentimentGrad)" name="提及次数" />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
