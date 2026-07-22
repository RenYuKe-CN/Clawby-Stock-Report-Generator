"use client";

import { useEffect, useState, useCallback } from "react";
import { Plus, Edit3, Trash2, Copy, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { ReportTemplate, ReportTemplateCreate, SectionDef, Language } from "@/types";

export default function TemplatesPage() {
  const [templates, setTemplates] = useState<ReportTemplate[]>([]);
  const [loading, setLoading] = useState(true);

  // Editor state
  const [editing, setEditing] = useState<ReportTemplate | null>(null);
  const [editForm, setEditForm] = useState<ReportTemplateCreate>({
    name: "",
    description: "",
    sections: [],
    system_prompt: "",
    user_prompt_template: "",
    required_data: [],
    optional_data: [],
    language: ["zh-CN", "en"],
    output_format: "markdown",
  });

  const load = useCallback(() => {
    api.listTemplates()
      .then(setTemplates)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const startEdit = (t: ReportTemplate) => {
    setEditing(t);
    setEditForm({
      name: t.name,
      description: t.description,
      sections: t.sections,
      system_prompt: t.system_prompt,
      user_prompt_template: t.user_prompt_template,
      required_data: t.required_data,
      optional_data: t.optional_data || [],
      language: t.language,
      output_format: t.output_format,
    });
  };

  const cancelEdit = () => {
    setEditing(null);
  };

  const handleSave = async () => {
    if (!editing) return;
    try {
      // For builtin templates, copy first
      if (editing.category === "builtin") {
        const copy = await api.copyTemplate(editing.id);
        await api.updateTemplate(copy.id, editForm);
      } else {
        await api.updateTemplate(editing.id, editForm);
      }
      cancelEdit();
      load();
    } catch (err: unknown) {
      alert((err as Error).message);
    }
  };

  const handleCopy = async (id: string) => {
    try {
      await api.copyTemplate(id);
      load();
    } catch (err: unknown) {
      alert((err as Error).message);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm("确认删除此模板?")) return;
    try {
      await api.deleteTemplate(id);
      load();
    } catch (err: unknown) {
      alert((err as Error).message);
    }
  };

  const openNew = () => {
    setEditing({
      id: "",
      name: "新模板",
      description: "",
      category: "custom",
      sections: [],
      system_prompt: "",
      user_prompt_template: "",
      required_data: ["quote", "bars"],
      optional_data: [],
      language: ["zh-CN", "en"],
      output_format: "markdown",
      created_at: "",
      updated_at: "",
      version: 1,
    });
    setEditForm({
      name: "新模板",
      description: "",
      sections: [],
      system_prompt: "",
      user_prompt_template: "",
      required_data: ["quote", "bars"],
      optional_data: [],
      language: ["zh-CN", "en"],
      output_format: "markdown",
    });
  };

  const dataDimLabels: Record<string, string> = {
    quote: "行情", bars: "日线", short: "做空", darkpool: "暗池",
    options: "期权", financials: "基本面", sentiment: "情绪", corporate: "公司行动",
  };

  if (loading) {
    return <div className="flex items-center justify-center h-64"><Loader2 size={24} className="animate-spin text-[#7c8db5]" /></div>;
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-semibold text-[#e2e8f0]">报告模板</h1>
        <button onClick={openNew} className="btn-primary flex items-center gap-2 text-sm">
          <Plus size={16} /> 新建模板
        </button>
      </div>

      {/* Editor */}
      {editing && (
        <div className="card-elevated p-5 space-y-4">
          <h2 className="text-sm font-medium text-[#e2e8f0]">
            {editing.category === "builtin" ? "复制内置模板并编辑" : "编辑模板"}
          </h2>

          <div className="grid grid-cols-2 gap-3">
            <div className="space-y-1 col-span-2">
              <label className="text-xs text-[#7c8db5]">模板名称</label>
              <input type="text" value={editForm.name}
                onChange={(e) => setEditForm({ ...editForm, name: e.target.value })}
                className="w-full" />
            </div>
            <div className="space-y-1 col-span-2">
              <label className="text-xs text-[#7c8db5]">描述</label>
              <input type="text" value={editForm.description}
                onChange={(e) => setEditForm({ ...editForm, description: e.target.value })}
                className="w-full" />
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#7c8db5]">必需数据维度</label>
              <div className="flex flex-wrap gap-1.5">
                {Object.entries(dataDimLabels).map(([key, label]) => (
                  <label key={key} className="flex items-center gap-1 text-xs text-[#7c8db5] cursor-pointer">
                    <input type="checkbox"
                      checked={editForm.required_data.includes(key)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setEditForm({ ...editForm, required_data: [...editForm.required_data, key] });
                        } else {
                          setEditForm({ ...editForm, required_data: editForm.required_data.filter((d) => d !== key) });
                        }
                      }}
                      className="accent-[#3b82f6]" />
                    {label}
                  </label>
                ))}
              </div>
            </div>
            <div className="space-y-1">
              <label className="text-xs text-[#7c8db5]">SSystem Prompt</label>
              <textarea value={editForm.system_prompt}
                onChange={(e) => setEditForm({ ...editForm, system_prompt: e.target.value })}
                className="w-full h-32 text-xs font-mono" />
            </div>
            <div className="space-y-1 col-span-2">
              <label className="text-xs text-[#7c8db5]">User Prompt Template</label>
              <textarea value={editForm.user_prompt_template}
                onChange={(e) => setEditForm({ ...editForm, user_prompt_template: e.target.value })}
                className="w-full h-32 text-xs font-mono" />
            </div>
          </div>

          <div className="flex items-center gap-2 justify-end">
            <button onClick={cancelEdit} className="btn-secondary text-sm">取消</button>
            <button onClick={handleSave} className="btn-primary text-sm">
              {editing.category === "builtin" ? "复制并保存" : "保存"}
            </button>
          </div>
        </div>
      )}

      {/* Template list */}
      <div className="space-y-3">
        {templates.map((t) => (
          <div key={t.id} className="card p-4 flex items-start justify-between">
            <div className="flex-1">
              <div className="flex items-center gap-2 mb-1">
                <span className="text-sm font-medium text-[#e2e8f0]">{t.name}</span>
                {t.category === "builtin" && (
                  <span className="text-[10px] bg-[#2d3748] text-[#7c8db5] px-1.5 py-0.5 rounded">内置</span>
                )}
                <span className="text-[10px] text-[#4a5568]">v{t.version}</span>
              </div>
              <p className="text-xs text-[#7c8db5] mb-1">{t.description}</p>
              <div className="flex items-center gap-2 text-xs text-[#4a5568]">
                <span>{t.sections.length} 章节</span>
                <span>·</span>
                <span>{t.required_data.length} 数据维度</span>
                <span>·</span>
                <span>语言: {t.language.join(", ")}</span>
              </div>
            </div>
            <div className="flex items-center gap-1">
              <button onClick={() => startEdit(t)}
                className="btn-secondary px-2 py-1 text-xs" title="编辑">
                <Edit3 size={14} />
              </button>
              <button onClick={() => handleCopy(t.id)}
                className="btn-secondary px-2 py-1 text-xs" title="复制">
                <Copy size={14} />
              </button>
              {t.category !== "builtin" && (
                <button onClick={() => handleDelete(t.id)}
                  className="btn-secondary px-2 py-1 text-xs text-[#ef5350]" title="删除">
                  <Trash2 size={14} />
                </button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
