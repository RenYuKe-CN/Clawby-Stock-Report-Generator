"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Cell,
} from "recharts";
import { Loader2 } from "lucide-react";

interface Props {
  ticker: string;
}

interface LevelData {
  price: string;
  volume: number;
  trades: number;
}

export default function ChartDarkPool({ ticker }: Props) {
  const [data, setData] = useState<LevelData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const today = new Date().toISOString().slice(0, 10);
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/darkpool/${ticker}?date=${today}`)
      .then((r) => r.json())
      .then((res) => {
        const levels = (res.levels || []) as Array<Record<string, unknown>>;
        const parsed: LevelData[] = levels
          .map((l) => ({
            price: String(l.price || l.level || ""),
            volume: Number(l.volume || l.vol || 0),
            trades: Number(l.trades || l.trade_count || 0),
          }))
          .sort((a, b) => Number(a.price) - Number(b.price))
          .slice(-30); // last 30 levels
        setData(parsed);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [ticker]);

  if (loading) {
    return <div className="skeleton" style={{ height: 220 }} />;
  }
  if (data.length === 0) {
    return <div className="text-xs text-[#4a5568] text-center py-8">今日暂无暗池数据</div>;
  }

  const maxVol = Math.max(...data.map(d => d.volume));

  return (
    <div className="space-y-1">
      <div className="text-xs text-[#7c8db5] mb-1">暗池价格分布 · 成交量 (股)</div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data} layout="vertical" margin={{ left: 50 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" horizontal={false} />
          <XAxis type="number" tick={{ fill: "#4a5568", fontSize: 10 }} />
          <YAxis type="category" dataKey="price" tick={{ fill: "#4a5568", fontSize: 10 }} tickLine={false} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1a1d2e", border: "1px solid #2d3748", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#e2e8f0" }}
            formatter={(value: number) => [value.toLocaleString(), "成交量"]}
          />
          <Bar dataKey="volume" maxBarSize={12} radius={[0, 3, 3, 0]}>
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.volume / maxVol > 0.7 ? "#3b82f6" : entry.volume / maxVol > 0.3 ? "#1a73e8" : "#2d3748"} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
