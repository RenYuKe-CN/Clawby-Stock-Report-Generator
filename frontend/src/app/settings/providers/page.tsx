"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Plus, Edit3, Trash2, CheckCircle, XCircle, RefreshCw,
  Star, Loader2,
} from "lucide-react";
import { api } from "@/lib/api";
import type { LLMProvider, LLMProviderCreate, ProviderType } from "@/types";

export default function ProvidersPage() {
  const [providers, setProviders] = useState<LLMProvider[]>([]);
  const [loading, setLoading] = useState(true);
  const [testing, setTesting] = useState<string | null>(null);

  // Form state
  const [showForm, setShowForm] = useState(false);
  const [editId, setEditId] = useState<string | null>(null);
  const [formData, setFormData] = useState<LLMProviderCreate>({
    name: "",
    provider_type: "openai",
    api_base: "https://api.openai.com/v1",
    api_key: "",
    default_model: "gpt-4o",
    supported_models: [],
  });

  const load = useCallback(() => {
    api.listProviders()
      .then(setProviders)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const resetForm = () => {
    setShowForm(false);
    setEditId(null);
    setFormData({
      name: "",
      provider_type: "openai",
      api_base: "https://api.openai.com/v1",
      api_key: "",
      default_model: "gpt-4o",
      supported_models: [],
    });
  };

  const handleSave = async () => {
    try {
      if (editId) {
        await api.updateProvider(editId, formData);
      } else {
        await api.createProvider(formData);
      }
      resetForm();
      load();
    } catch (err: unknown) {
      alert((err as Error).message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确认删除此 Provider?")) return;
    try {
      await api.deleteProvider(id);
      load();
    } catch (err: unknown) {
      alert((err as Error).message);
    }
  };

  const handleSetDefault = async (id: string) => {
    try {
      await api.setDefaultProvider(id);
      load();
    } catch (err: unknown) {
      alert((err as Error).message);
    }
  };

  const handleTest = async (id: string) => {
    setTesting(id);
    try {
      await api.testProvider(id);
      load();
    } catch (err: unknown) {
      alert((err as Error).message);
    } finally {
      setTesting(null);
    }
  };

  const handleEdit = (p: LLMProvider) => {
    setEditId(p.id);
    setFormData({
      name: p.name,
      provider_type: p.provider_type,
      api_base: p.api_base,
      api_key: "",
      default_model: p.default_model,
      supported_models: p.supported_models,
    });
    setShowForm(true);
  };

  const providerTypeLabel: Record<ProviderType, string> = {
    openai: "OpenAI",
    anthropic: "Anthropic",
    custom_openai: "自定义 (OpenAI 兼容)",
    custom_anthropic: "自定义 (Anthropic 兼容)",
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 size={24} className="animate-spin text-[#7c8db5]" /></div>;
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#e2e8f0]">LLM Providers</h1>
        <button onClick={() => { resetForm(); setShowForm(true); }} className="btn-primary flex items-center gap-2 text-sm">
          <Plus size={16} /> 添加 Provider
        </button>
      </div>

      {/* Form modal */}
      {showForm && (
        <div className="card-elevated p-5 space-y-4">
          <h2 className="text-sm font-medium text-[#e2e8f0]">{editId ? "编辑 Provider" : "添加 Provider"}</h2>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1">
              <label className="text-xs text-[#7c8db5]">名称</label>
              <input type="text" value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="w-full" placeholder="如: 我的 OpenAI" />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#7c8db5]">类型</label>
              <select value={formData.provider_type}
                onChange={(e) => setFormData({ ...formData, provider_type: e.target.value as ProviderType })}
                className="w-full">
                {Object.entries(providerTypeLabel).map(([k, v]) => (
                  <option key={k} value={k}>{v}</option>
                ))}
              </select>
            </div>
            <div className="space-y-1 col-span-2">
              <label className="text-xs text-[#7c8db5]">API Base URL</label>
              <input type="text" value={formData.api_base}
                onChange={(e) => setFormData({ ...formData, api_base: e.target.value })}
                className="w-full" placeholder="https://api.openai.com/v1" />
            </div>
            <div className="space-y-1 col-span-2">
              <label className="text-xs text-[#7c8db5]">API Key</label>
              <input type="password" value={formData.api_key}
                onChange={(e) => setFormData({ ...formData, api_key: e.target.value })}
                className="w-full" placeholder={editId ? "留空则不修改" : "sk-..."} />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#7c8db5]">默认模型</label>
              <input type="text" value={formData.default_model}
                onChange={(e) => setFormData({ ...formData, default_model: e.target.value })}
                className="w-full" placeholder="gpt-4o" />
            </div>
          </div>

          <div className="flex items-center gap-2 justify-end">
            <button onClick={resetForm} className="btn-secondary text-sm">取消</button>
            <button onClick={handleSave} className="btn-primary text-sm">保存</button>
          </div>
        </div>
      )}

      {/* Provider list */}
      <div className="space-y-3">
        {providers.length === 0 && (
          <div className="card p-8 text-center text-[#4a5568]">
            还没有配置 LLM Provider。点击上方按钮添加。
          </div>
        )}
        {providers.map((p) => (
          <div key={p.id} className="card p-4 flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                {p.is_available ? (
                  <CheckCircle size={14} className="text-[#26a69a]" />
                ) : (
                  <XCircle size={14} className="text-[#ef5350]" />
                )}
                <span className="text-sm font-medium text-[#e2e8f0]">{p.name}</span>
                {p.is_default && (
                  <span className="text-[10px] bg-[#1a73e8]/20 text-[#3b82f6] px-1.5 py-0.5 rounded">默认</span>
                )}
              </div>
              <div className="text-xs text-[#7c8db5] space-y-0.5">
                <div>{providerTypeLabel[p.provider_type]} · {p.api_base}</div>
                <div>模型: {p.default_model}</div>
                {p.error_message && <div className="text-[#ef5350]">错误: {p.error_message}</div>}
                {p.last_tested_at && (
                  <div>上次测试: {new Date(p.last_tested_at).toLocaleString()}</div>
                )}
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => handleTest(p.id)} disabled={testing === p.id}
                className="btn-secondary px-2 py-1 text-xs" title="测试连接">
                {testing === p.id ? <Loader2 size={14} className="animate-spin" /> : <RefreshCw size={14} />}
              </button>
              {!p.is_default && (
                <button onClick={() => handleSetDefault(p.id)}
                  className="btn-secondary px-2 py-1 text-xs" title="设为默认">
                  <Star size={14} />
                </button>
              )}
              <button onClick={() => handleEdit(p)}
                className="btn-secondary px-2 py-1 text-xs" title="编辑">
                <Edit3 size={14} />
              </button>
              <button onClick={() => handleDelete(p.id)}
                className="btn-secondary px-2 py-1 text-xs text-[#ef5350]" title="删除">
                <Trash2 size={14} />
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
