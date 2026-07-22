"use client";

import { useEffect, useState } from "react";
import {
  LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer,
  CartesianGrid, Legend,
} from "recharts";
import { api } from "@/lib/api";
import { Loader2 } from "lucide-react";

interface Props {
  ticker: string;
}

interface ShortPoint {
  date: string;
  shortRatio: number | null;
  borrowFee: number | null;
  siRatio: number | null;
}

export default function ChartShort({ ticker }: Props) {
  const [data, setData] = useState<ShortPoint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/short/${ticker}`)
      .then((r) => r.json())
      .then((res) => {
        const sv = (res.short_volume || []) as Array<Record<string, unknown>>;
        const bf = (res.borrow_fee || []) as Array<Record<string, unknown>>;
        const si = (res.short_interest || []) as Array<Record<string, unknown>>;

        // Build date map
        const map = new Map<string, ShortPoint>();

        // Short volume ratio (short / total)
        sv.slice(0, 60).forEach((item) => {
          const date = String(item.date || "").slice(0, 10);
          const st = Number(item.st) || 0;
          const rt = Number(item.rt) || 1;
          map.set(date, { date, shortRatio: Math.round((st / rt) * 1000) / 10, borrowFee: null, siRatio: null });
        });

        // Borrow fee
        bf.slice(0, 60).forEach((item) => {
          const date = String(item.timestamp || item.date || "").slice(0, 10);
          const fee = Number(item.borrow_rate || item.fee || 0);
          const existing = map.get(date) || { date, shortRatio: null, borrowFee: null, siRatio: null };
          existing.borrowFee = Math.round(fee * 100) / 100;
          map.set(date, existing);
        });

        // SI ratio
        si.slice(0, 10).forEach((item) => {
          const date = String(item.date || "").slice(0, 10);
          const ratio = Number(item.short_pct || item.ratio || 0);
          const existing = map.get(date) || { date, shortRatio: null, borrowFee: null, siRatio: null };
          existing.siRatio = Math.round(ratio * 10) / 10;
          map.set(date, existing);
        });

        setData(Array.from(map.values()).sort((a, b) => a.date.localeCompare(b.date)));
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [ticker]);

  if (loading) {
    return <div className="skeleton" style={{ height: 250 }} />;
  }
  if (data.length === 0) {
    return <div className="text-xs text-[#4a5568] text-center py-8">暂无做空数据</div>;
  }

  return (
    <div className="space-y-1">
      <div className="text-xs text-[#7c8db5] mb-1">做空趋势 · 短成交量比 / 借券费率 / 空头比</div>
      <ResponsiveContainer width="100%" height={250}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#1f2937" />
          <XAxis dataKey="date" tick={{ fill: "#4a5568", fontSize: 10 }} tickLine={false} />
          <YAxis yAxisId="pct" domain={[0, 'auto']} tick={{ fill: "#4a5568", fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
          <YAxis yAxisId="fee" domain={[0, 'auto']} orientation="right" tick={{ fill: "#4a5568", fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
          <Tooltip
            contentStyle={{ backgroundColor: "#1a1d2e", border: "1px solid #2d3748", borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: "#e2e8f0" }}
          />
          <Legend wrapperStyle={{ fontSize: 11, color: "#7c8db5" }} />
          <Line yAxisId="pct" type="monotone" dataKey="shortRatio" stroke="#ffa726" strokeWidth={2} dot={false} name="短成交量比" />
          <Line yAxisId="pct" type="monotone" dataKey="siRatio" stroke="#ef5350" strokeWidth={2} dot={false} name="空头比" />
          <Line yAxisId="fee" type="monotone" dataKey="borrowFee" stroke="#26a69a" strokeWidth={2} dot={false} name="借券费率" />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
