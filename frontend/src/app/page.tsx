"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/navigation";
import { Send, Loader2, BarChart3 } from "lucide-react";
import { api, streamReport } from "@/lib/api";
import ReportViewer from "@/components/report/report-viewer";
import type {
  LLMProvider,
  ReportTemplate,
  ReportRequest,
} from "@/types";

const RECENT_TICKERS_KEY = "recent_tickers";

export default function HomePage() {
  const router = useRouter();

  const [ticker, setTicker] = useState("");
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [selectedTemplate, setSelectedTemplate] = useState("rpt_comprehensive");
  const [selectedProvider, setSelectedProvider] = useState("");
  const [selectedModel, setSelectedModel] = useState("");
  const [selectedLang, setSelectedLang] = useState<"zh-CN" | "en">("zh-CN");
  const [recentTickers, setRecentTickers] = useState<string[]>([]);
  const [generating, setGenerating] = useState(false);
  const [progressMsg, setProgressMsg] = useState("");
  const [progressPct, setProgressPct] = useState(0);
  const [reportMd, setReportMd] = useState("");
  const [errorMsg, setErrorMsg] = useState("");
  const reportRef = useRef<HTMLDivElement>(null);
  const controllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    api.listTemplates().then(setTemplates).catch(() => {});
    api.listProviders().then((list) => {
      setProviders(list);
      const def = list.find((p) => p.is_default);
      if (def) {
        setSelectedProvider(def.id);
        setSelectedModel(def.default_model);
      }
    }).catch(() => {});
    const saved = localStorage.getItem(RECENT_TICKERS_KEY);
    if (saved) setRecentTickers(JSON.parse(saved));
  }, []);

  const handleGenerate = useCallback(() => {
    const tk = ticker.trim().toUpperCase();
    if (!tk) return;
    if (!selectedProvider) {
      setErrorMsg("请先配置 LLM Provider");
      return;
    }
    setGenerating(true);
    setReportMd("");
    setErrorMsg("");
    setProgressMsg("正在验证...");
    setProgressPct(0);

    const updated = [tk, ...recentTickers.filter((t) => t !== tk)].slice(0, 5);
    setRecentTickers(updated);
    localStorage.setItem(RECENT_TICKERS_KEY, JSON.stringify(updated));

    const req: ReportRequest = {
      ticker: tk,
      template_id: selectedTemplate,
      provider_id: selectedProvider,
      model: selectedModel,
      language: selectedLang,
    };

    // Timeout: abort if no data for 30s
    const timeoutTimer = setTimeout(() => {
      if (controllerRef.current) {
        controllerRef.current.abort();
        setGenerating(false);
        setErrorMsg("报告生成超时，请检查 LLM Provider 配置和网络连接");
        setProgressMsg("");
      }
    }, 35000);

    controllerRef.current = streamReport(
      req,
      (evt) => { setProgressMsg(evt.message); setProgressPct(evt.progress); },
      (evt) => { clearTimeout(timeoutTimer); setReportMd((prev) => prev + evt.text); },
      (evt) => {
        setGenerating(false);
        setProgressMsg("生成完成");
        setProgressPct(100);
        router.replace(`/report/${evt.id}`);
      },
      (evt) => {
        clearTimeout(timeoutTimer);
        setGenerating(false);
        setErrorMsg(evt.message || "报告生成失败，请检查配置");
        setProgressMsg("");
      }
    );
  }, [ticker, selectedTemplate, selectedProvider, selectedModel, selectedLang, recentTickers, router]);

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* ── Hero Input ──────────────────────────────── */}
      <div className="card p-6">
        <h1 className="text-xl font-semibold text-[#e2e8f0] mb-1">美股分析报告生成器</h1>
        <p className="text-sm text-[#7c8db5] mb-5">输入股票代码，基于 Clawby 实时数据 + AI 生成专业分析报告</p>

        <div className="flex items-center gap-3 mb-4">
          <div className="relative flex-1 max-w-md">
            <input
              type="text"
              value={ticker}
              onChange={(e) => setTicker(e.target.value.toUpperCase())}
              onKeyDown={(e) => e.key === "Enter" && handleGenerate()}
              placeholder="输入股票代码 e.g. AAPL, MSFT, TSLA"
              className="w-full pl-4 pr-4 py-3 bg-[#1a1d2e] border border-[#2d3748] rounded-lg text-[#e2e8f0] placeholder-[#4a5568] text-base focus:border-[#3b82f6] outline-none"
              disabled={generating}
            />
          </div>
          <button onClick={handleGenerate} disabled={generating || !ticker.trim() || !selectedProvider}
            className="btn-primary flex items-center gap-2 px-6 py-3 text-base">
            {generating ? <Loader2 size={18} className="animate-spin" /> : <Send size={18} />}
            {generating ? "生成中..." : "生成报告"}
          </button>
        </div>

        <div className="flex items-center gap-4 flex-wrap">
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#7c8db5]">模板:</span>
            <select value={selectedTemplate} onChange={(e) => setSelectedTemplate(e.target.value)}
              className="bg-[#1a1d2e] border border-[#2d3748] rounded px-3 py-1.5 text-sm text-[#e2e8f0]" disabled={generating}>
              {templates.map((t) => <option key={t.id} value={t.id}>{t.name}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#7c8db5]">LLM:</span>
            <select value={selectedProvider} onChange={(e) => {
              setSelectedProvider(e.target.value);
              const p = providers.find((pr) => pr.id === e.target.value);
              if (p) setSelectedModel(p.default_model);
            }} className="bg-[#1a1d2e] border border-[#2d3748] rounded px-3 py-1.5 text-sm text-[#e2e8f0]" disabled={generating}>
              {providers.map((p) => <option key={p.id} value={p.id}>{p.name} {p.is_available ? "" : "(未测试)"}</option>)}
            </select>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-[#7c8db5]">模型:</span>
            <input type="text" value={selectedModel} onChange={(e) => setSelectedModel(e.target.value)}
              className="bg-[#1a1d2e] border border-[#2d3748] rounded px-3 py-1.5 text-sm text-[#e2e8f0] w-48" disabled={generating} />
          </div>
          <select value={selectedLang} onChange={(e) => setSelectedLang(e.target.value as "zh-CN" | "en")}
            className="bg-[#1a1d2e] border border-[#2d3748] rounded px-3 py-1.5 text-sm text-[#e2e8f0]" disabled={generating}>
            <option value="zh-CN">中文</option>
            <option value="en">English</option>
          </select>
        </div>

        {recentTickers.length > 0 && (
          <div className="flex items-center gap-2 mt-3">
            <span className="text-xs text-[#4a5568]">最近:</span>
            {recentTickers.map((tk) => (
              <button key={tk} onClick={() => setTicker(tk)}
                className="text-xs text-[#7c8db5] hover:text-[#3b82f6] bg-[#1a1d2e] px-2 py-1 rounded">{tk}</button>
            ))}
          </div>
        )}
      </div>

      {/* ── Progress ───────────────────────────────── */}
      {generating && (
        <div className="card p-4 space-y-2">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[#7c8db5]">{progressMsg}</span>
            <span className="text-[#3b82f6] font-mono">{progressPct}%</span>
          </div>
          <div className="w-full h-1.5 bg-[#1f2937] rounded-full overflow-hidden">
            <div className="h-full bg-[#3b82f6] rounded-full transition-all duration-300" style={{ width: `${progressPct}%` }} />
          </div>
        </div>
      )}

      {/* ── Error ──────────────────────────────────── */}
      {errorMsg && (
        <div className="card p-4 border-[#ef5350]/30">
          <p className="text-sm text-[#ef5350]">{errorMsg}</p>
        </div>
      )}

      {/* ── Report Output ──────────────────────────── */}
      {reportMd && (
        <div className="card p-6" ref={reportRef}>
          <ReportViewer markdown={reportMd} ticker={ticker.toUpperCase()} />
        </div>
      )}

      {/* ── Empty state ────────────────────────── */}
      {!reportMd && !generating && !errorMsg && (
        <div className="card p-12 text-center">
          <BarChart3 size={48} className="mx-auto mb-4 text-[#2d3748]" />
          <p className="text-[#7c8db5]">输入股票代码，点击「生成报告」获取 AI 分析</p>
          <p className="text-xs text-[#4a5568] mt-2">数据来源: Clawby · 支持 OpenAI / Anthropic / 自定义模型</p>
        </div>
      )}
    </div>
  );
}
