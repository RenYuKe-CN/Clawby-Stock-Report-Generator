"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { ArrowLeft, Download, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import ReportViewer from "@/components/report/report-viewer";

interface ReportDetail {
  id: string;
  ticker: string;
  template_id: string;
  template_name: string;
  provider_name: string;
  model: string;
  language: string;
  markdown: string;
  generated_at: string;
}

export default function ReportDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [report, setReport] = useState<ReportDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const id = params?.id as string;
    if (!id) return;
    api.getReport(id)
      .then((data) => { setReport(data as unknown as ReportDetail); setLoading(false); })
      .catch((err) => { setError(err.message); setLoading(false); });
  }, [params]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 size={24} className="animate-spin text-[#7c8db5]" />
      </div>
    );
  }

  if (error || !report) {
    return (
      <div className="card p-6">
        <p className="text-[#ef5350]">加载失败: {error || "报告未找到"}</p>
        <button onClick={() => router.push("/")} className="btn-primary mt-4">返回首页</button>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <button onClick={() => router.push("/")} className="btn-secondary flex items-center gap-1 px-3 py-1.5 text-sm">
            <ArrowLeft size={16} /> 返回
          </button>
          <h1 className="text-lg font-semibold text-[#e2e8f0]">
            {report.ticker} &mdash; {report.template_name}
          </h1>
        </div>
        <button onClick={() => {
          const blob = new Blob([report.markdown], { type: "text/markdown" });
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = `${report.ticker}_report_${report.generated_at.slice(0, 10)}.md`;
          a.click();
          URL.revokeObjectURL(url);
        }} className="btn-primary flex items-center gap-2 text-sm">
          <Download size={16} /> Markdown
        </button>
          <a
            href={`http://localhost:8000/api/report/${report.id}/pdf`}
            target="_blank"
            rel="noopener noreferrer"
            className="btn-primary flex items-center gap-2 text-sm"
          >
            <Download size={16} /> 下载 PDF
          </a>
      </div>

      <div className="flex items-center gap-4 text-xs text-[#7c8db5]">
        <span>生成于: {new Date(report.generated_at).toLocaleString()}</span>
        <span>模型: {report.provider_name} / {report.model}</span>
        <span>模板: {report.template_name}</span>
      </div>

      <div className="card p-6">
        <ReportViewer markdown={report.markdown} ticker={report.ticker} />
      </div>
    </div>
  );
}
