"use client";

import { useEffect, useState } from "react";
import { CheckCircle, XCircle, Loader2 } from "lucide-react";
import { api } from "@/lib/api";
import type { LLMProvider, HealthResponse } from "@/types";

export default function Topbar() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [defaultProv, setDefaultProv] = useState<LLMProvider | null>(null);

  useEffect(() => {
    api.health().then(setHealth).catch(() => {});
    api.listProviders().then((list) => {
      const def = list.find((p) => p.is_default);
      if (def) setDefaultProv(def);
    }).catch(() => {});
  }, []);

  return (
    <header className="h-14 border-b border-[#1f2937] flex items-center justify-between px-6 bg-[#0a0e17]">
      {/* Left: page breadcrumb placeholder */}
      <div />

      {/* Right: status indicators */}
      <div className="flex items-center gap-5 text-xs">
        {/* Clawby status */}
        <div className="flex items-center gap-1.5">
          <span className="text-[#7c8db5]">Clawby</span>
          {!health ? (
            <Loader2 size={14} className="animate-spin text-[#7c8db5]" />
          ) : health.clawby_status === "ok" ? (
            <CheckCircle size={14} className="text-[#26a69a]" />
          ) : (
            <XCircle size={14} className="text-[#ef5350]" />
          )}
        </div>

        {/* LLM provider indicator */}
        <div className="flex items-center gap-1.5">
          {defaultProv ? (
            <>
              <span className={`status-dot ${defaultProv.is_available ? "green" : "yellow"}`} />
              <span className="text-[#7c8db5]">{defaultProv.name}</span>
              <span className="text-[#4a5568]">{defaultProv.default_model}</span>
            </>
          ) : (
            <span className="text-[#ef5350]">未配置 LLM</span>
          )}
        </div>
      </div>
    </header>
  );
}
