"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  ComposedChart, CartesianGrid, Legend,
} from "recharts";
import { api } from "@/lib/api";
import { Loader2 } from "lucide-react";

interface Props {
  ticker: string;
}

interface BarData {
  date: string;
  close: number;
  volume: number;
  ma20: number | null;
  ma50: number | null;
}

export default function ChartPrice({ ticker }: Props) {
  const [data, setData] = useState<BarData[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.bars(ticker)
      .then((res) => {
        const bars = res.bars.slice(-200); // last 200 days
        const parsed: BarData[] = bars.map((b: Record<string, unknown>, i: number) => {
          const close = Number(b.c) || Number(b.close) || 0;
          const volume = Number(b.v) || Number(b.volume) || 0;
          const date = String(b.t || b.date || "").slice(0, 10);
          return { date, close, volume, ma20: null, ma50: null };
        });

        // Calculate MA20 and MA50
        const calcMA = (arr: BarData[], period: number): (number | null)[] => {
          return arr.map((_, i) => {
            if (i < period - 1) return null;
            let sum = 0;
            for (let j = 0; j < period; j++) sum += arr[i - j].close;
            return Math.round((sum / period) * 100) / 100;
          });
        };

        const ma20 = calcMA(parsed, 20);
        const ma50 = calcMA(parsed, 50);
        parsed.forEach((d, i) => { d.ma20 = ma20[i]; d.ma50 = ma50[i]; });

        setData(parsed.slice(-90)); // Show last 90 days
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [ticker]);

  if (loading) {
    return <div className="skeleton" style={{ height: 300 }} />;
  }
  if (data.length === 0) {
    return <div className="text-xs text-[#4a5568] text-center py-8">暂无价格数据</div>;
  }

  const minPrice = Math.min(...data.map(d => d.close)) * 0.97;
  const maxPrice = Math.max(...data.map(d => d.close)) * 1.03;
  const maxVol = Math.max(...data.map(d => d.volume));

  return (
    <div className="space-y-1">
      <div className="text-xs text-[#7c8db5] mb-1">{ticker} 价格走势 · MA20 / MA50</div>
      <ResponsiveContainer width="100%" height={300}>
        <ComposedChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" tick={{ fill: "#4a5568", fontSize: 10 }} tickLine={false} />
          <YAxis
            yAxisId="price"
            domain={[minPrice, maxPrice]}
            tick={{ fill: "#4a5568", fontSize: 10 }}
            orientation="right"
            tickFormatter={(v) => `$${v.toFixed(0)}`}
          />
          <YAxis
            yAxisId="volume"
            domain={[0, maxVol * 3]}
            hide
          />
          <Tooltip
            contentStyle={{ backgroundColor: "#1a1d2e", border: "1px solid #2d3748", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: "#7c8db5" }} />
          <Bar yAxisId="volume" dataKey="volume" fill="#1f2937" opacity={0.5} barSize={4} />
          <Line yAxisId="price" type="monotone" dataKey="close" stroke="#3b82f6" strokeWidth={2} dot={false} name="价格" />
          <Line yAxisId="price" type="monotone" dataKey="ma20" stroke="#ffa726" strokeWidth={1.5} dot={false} strokeDasharray="4 2" name="MA20" />
          <Line yAxisId="price" type="monotone" dataKey="ma50" stroke="#ef5350" strokeWidth={1.5} dot={false} strokeDasharray="4 2" name="MA50" />
        </ComposedChart>
      </ResponsiveContainer>
    </div>
  );
}
