"use client";

import { useEffect, useState } from "react";
import { Settings, Key, CheckCircle, XCircle, Loader2, Save } from "lucide-react";
import Link from "next/link";
import { api } from "@/lib/api";

export default function SettingsPage() {
  const [clawbyKey, setClawbyKey] = useState("");
  const [clawbyConfigured, setClawbyConfigured] = useState(false);
  const [clawbyPreview, setClawbyPreview] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [statusMsg, setStatusMsg] = useState("");
  const [testResult, setTestResult] = useState<{ success: boolean; message: string; latency_ms: number | null } | null>(null);

  const loadConfig = async () => {
    try {
      const cfg = await api.clawbyConfig();
      setClawbyConfigured(cfg.configured);
      setClawbyPreview(cfg.api_key_preview);
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadConfig(); }, []);

  const handleSave = async () => {
    if (!clawbyKey.trim()) return;
    setSaving(true);
    setStatusMsg("");
    try {
      const res = await api.updateClawbyKey(clawbyKey.trim());
      setStatusMsg(res.message);
      setClawbyKey("");
      await loadConfig();
    } catch (err: unknown) {
      setStatusMsg((err as Error).message);
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    setTesting(true);
    setTestResult(null);
    try {
      const res = await api.testClawby();
      setTestResult(res);
    } catch (err: unknown) {
      setTestResult({ success: false, message: (err as Error).message, latency_ms: null });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <h1 className="text-xl font-semibold text-[#e2e8f0] flex items-center gap-2">
        <Settings size={22} /> 设置
      </h1>

      {/* ── Clawby Configuration ─────────────────────────────────────── */}
      <div className="card p-5 space-y-4">
        <h2 className="text-sm font-medium text-[#e2e8f0] flex items-center gap-2">
          <Key size={16} /> Clawby API 配置
        </h2>

        {loading ? (
          <div className="flex items-center gap-2 text-xs text-[#7c8db5]">
            <Loader2 size={14} className="animate-spin" /> 加载中...
          </div>
        ) : (
          <>
            {/* Status */}
            <div className="flex items-center gap-2 text-sm">
              <span className="text-[#7c8db5]">状态:</span>
              {clawbyConfigured ? (
                <span className="flex items-center gap-1 text-[#26a69a]">
                  <CheckCircle size={14} /> 已配置
                  {clawbyPreview && <span className="text-xs text-[#4a5568]">({clawbyPreview})</span>}
                </span>
              ) : (
                <span className="flex items-center gap-1 text-[#ef5350]">
                  <XCircle size={14} /> 未配置
                </span>
              )}
            </div>

            {/* Key input */}
            <div className="flex items-center gap-2">
              <input
                type="password"
                value={clawbyKey}
                onChange={(e) => setClawbyKey(e.target.value)}
                placeholder="输入新的 Clawby API Key（pk_...）"
                className="flex-1 bg-[#1a1d2e] border border-[#2d3748] rounded px-3 py-2 text-sm text-[#e2e8f0] placeholder-[#4a5568]"
              />
              <button
                onClick={handleSave}
                disabled={saving || !clawbyKey.trim()}
                className="btn-primary flex items-center gap-1.5 text-sm px-4 py-2"
              >
                {saving ? <Loader2 size={14} className="animate-spin" /> : <Save size={14} />}
                保存
              </button>
            </div>

            {/* Test connection */}
            <div className="flex items-center gap-3">
              <button
                onClick={handleTest}
                disabled={testing || !clawbyConfigured}
                className="btn-secondary flex items-center gap-1.5 text-sm px-3 py-1.5"
              >
                {testing ? <Loader2 size={14} className="animate-spin" /> : null}
                测试连接
              </button>
              {testResult && (
                <span className={`text-xs flex items-center gap-1 ${
                  testResult.success ? "text-[#26a69a]" : "text-[#ef5350]"
                }`}>
                  {testResult.success ? <CheckCircle size={12} /> : <XCircle size={12} />}
                  {testResult.message}
                  {testResult.latency_ms != null && ` (${testResult.latency_ms}ms)`}
                </span>
              )}
            </div>

            {statusMsg && (
              <p className="text-xs text-[#7c8db5]">{statusMsg}</p>
            )}

            <p className="text-xs text-[#4a5568]">
              免费注册 Clawby 账号: <a href="https://www.openclawby.com/" target="_blank" rel="noopener noreferrer" className="text-[#3b82f6] hover:underline">https://www.openclawby.com/</a>
            </p>
          </>
        )}
      </div>

      {/* ── Navigation cards ─────────────────────────────────────────── */}
      <div className="grid gap-4">
        <Link href="/settings/providers" className="card p-5 hover:border-[#3b82f6]/50 transition-colors no-underline block">
          <h2 className="text-base font-medium text-[#e2e8f0] mb-1">LLM Providers</h2>
          <p className="text-sm text-[#7c8db5]">管理 AI 模型提供商配置（OpenAI / Anthropic / 自定义）</p>
        </Link>

        <Link href="/settings/templates" className="card p-5 hover:border-[#3b82f6]/50 transition-colors no-underline block">
          <h2 className="text-base font-medium text-[#e2e8f0] mb-1">报告模板</h2>
          <p className="text-sm text-[#7c8db5]">自定义分析报告的章节、Prompt 和风格</p>
        </Link>
      </div>

      {/* ── About ────────────────────────────────────────────────────── */}
      <div className="card p-4">
        <h2 className="text-sm font-medium text-[#e2e8f0] mb-2">关于</h2>
        <p className="text-xs text-[#4a5568]">
          Clawby Stock Report Generator v0.2 · 数据来源 Clawby API · 开源 MIT License
        </p>
      </div>
    </div>
  );
}
