"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { BarChart3, FileText, History, Settings, FlaskConical } from "lucide-react";

const navItems = [
  { href: "/", label: "生成报告", icon: BarChart3 },
  { href: "/history", label: "历史报告", icon: History },
  { href: "/settings/providers", label: "LLM 配置", icon: FlaskConical },
  { href: "/settings/templates", label: "报告模板", icon: FileText },
  { href: "/settings", label: "设置", icon: Settings },
];

export default function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="w-56 min-h-screen bg-[#0a0e17] border-r border-[#1f2937] flex flex-col">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-[#1f2937]">
        <Link href="/" className="flex items-center gap-2 no-underline">
          <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
            <rect x="2" y="10" width="4" height="16" rx="1" fill="#3b82f6" />
            <rect x="8" y="6" width="4" height="20" rx="1" fill="#26a69a" />
            <rect x="14" y="14" width="4" height="12" rx="1" fill="#ffa726" />
            <rect x="20" y="2" width="4" height="24" rx="1" fill="#3b82f6" opacity="0.6" />
          </svg>
          <div>
            <div className="text-sm font-semibold text-[#e2e8f0]">Clawby Report</div>
            <div className="text-[10px] text-[#7c8db5]">Stock Analysis</div>
          </div>
        </Link>
      </div>

      {/* Navigation */}
      <nav className="flex-1 px-3 py-4 space-y-1">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors no-underline ${
                isActive
                  ? "bg-[#1a73e8]/10 text-[#3b82f6] font-medium"
                  : "text-[#7c8db5] hover:text-[#e2e8f0] hover:bg-[#111827]"
              }`}
            >
              <Icon size={18} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-5 py-3 border-t border-[#1f2937] text-[10px] text-[#4a5568]">
        v0.2 · Powered by Clawby
      </div>
    </aside>
  );
}
