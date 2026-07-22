"use client";

import { useEffect, useState } from "react";
import {
  BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend, Cell,
} from "recharts";
import { Loader2 } from "lucide-react";

interface Props {
  ticker: string;
}

interface StrikeData {
  strike: number;
  callOI: number;
  putOI: number;
}

export default function ChartOptions({ ticker }: Props) {
  const [data, setData] = useState<StrikeData[]>([]);
  const [loading, setLoading] = useState(true);
  const [maxPain, setMaxPain] = useState<number | null>(null);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/options/${ticker}`)
      .then((r) => r.json())
      .then((res) => {
        const chain = (res.chain || []) as Array<Record<string, unknown>>;
        setMaxPain(res.max_pain != null ? Number(res.max_pain) : null);

        const parsed: StrikeData[] = chain.map((item) => ({
          strike: Number(item.strike || item.strike_price || 0),
          callOI: Number(item.call_open_interest || item.call_oi || 0),
          putOI: Number(item.put_open_interest || item.put_oi || 0),
        })).sort((a, b) => a.strike - b.strike);

        setData(parsed);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [ticker]);

  if (loading) {
    return <div className="skeleton" style={{ height: 220 }} />;
  }
  if (data.length === 0) {
    return <div className="text-xs text-[#4a5568] text-center py-8">暂无期权链数据</div>;
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-[#7c8db5]">期权链 · Call / Put 未平仓量</span>
        {maxPain && <span className="text-xs text-[#ffa726]">Max Pain: ${maxPain}</span>}
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="strike" tick={{ fill: "#4a5568", fontSize: 10 }} tickFormatter={(v) => `$${v}`} />
          <YAxis tick={{ fill: "#4a5568", fontSize: 10 }} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1a1d2e", border: "1px solid #2d3748", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: "#7c8db5" }} />
          <Bar dataKey="callOI" fill="#26a69a" name="Call OI" radius={[3, 3, 0, 0]} />
          <Bar dataKey="putOI" fill="#ef5350" name="Put OI" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
