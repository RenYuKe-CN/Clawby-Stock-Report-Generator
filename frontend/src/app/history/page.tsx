"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { FileText, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { ReportListItem } from "@/types";

export default function HistoryPage() {
  const [reports, setReports] = useState<ReportListItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.listReports()
      .then(setReports)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 size={24} className="animate-spin text-[#7c8db5]" /></div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[#e2e8f0]">历史报告</h1>

      {reports.length === 0 ? (
        <div className="card p-8 text-center text-[#4a5568]">
          <FileText size={40} className="mx-auto mb-3 text-[#2d3748]" />
          <p>还没有生成过报告</p>
          <Link href="/" className="text-[#3b82f6] text-sm hover:underline mt-2 inline-block">
            前往生成第一份报告
          </Link>
        </div>
      ) : (
        <div className="space-y-2">
          {reports.map((r) => (
            <Link
              key={r.id}
              href={`/report/${r.id}`}
              className="card p-4 flex items-center justify-between no-underline hover:border-[#3b82f6]/50 transition-colors"
            >
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-semibold text-[#3b82f6]">{r.ticker}</span>
                  <span className="text-sm text-[#e2e8f0]">{r.template_name}</span>
                </div>
                <div className="text-xs text-[#7c8db5] mt-1">
                  {r.provider_name} / {r.model} · {r.language}
                </div>
              </div>
              <div className="text-xs text-[#4a5568]">
                {new Date(r.generated_at).toLocaleString()}
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}
