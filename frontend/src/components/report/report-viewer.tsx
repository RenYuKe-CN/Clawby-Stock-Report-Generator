"use client";

import React, { useState, useEffect } from "react";
import ChartPrice from "@/components/charts/chart-price";
import ChartShort from "@/components/charts/chart-short";
import ChartDarkPool from "@/components/charts/chart-darkpool";
import ChartOptions from "@/components/charts/chart-options";
import GaugeSentiment from "@/components/charts/gauge-sentiment";
import { Loader2 } from "lucide-react";

interface Props {
  markdown: string;
  ticker: string;
}

/**
 * Renders the report markdown as HTML, followed by ALL available charts
 * for the given ticker — regardless of whether the markdown contains
 * ![chart:...] placeholders.
 */
export default function ReportViewer({ markdown, ticker }: Props) {
  const [chartsLoaded, setChartsLoaded] = useState(false);

  useEffect(() => {
    // Short delay to let the DOM settle, then show charts
    const t = setTimeout(() => setChartsLoaded(true), 100);
    return () => clearTimeout(t);
  }, []);

  // Parse markdown for any ![chart:chart_id] placeholders and resolve them
  const segments = parseMarkdown(markdown);

  return (
    <div>
      {/* Markdown text content */}
      <div className="report-content">
        {segments.map((seg, i) => {
          if (seg.type === "chart") {
            return (
              <div key={`c-${i}`} className="card-elevated p-3 my-4">
                {renderChart(seg.chartId, ticker)}
              </div>
            );
          }
          return (
            <div key={`t-${i}`} dangerouslySetInnerHTML={{ __html: seg.html }} />
          );
        })}
      </div>

      {/* Always show all charts at the bottom */}
      <div className="mt-8 space-y-4">
        <h3 className="text-sm font-semibold text-[#e2e8f0] border-b border-[#1f2937] pb-2">
          数据图表
        </h3>

        {!chartsLoaded ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 size={20} className="animate-spin text-[#7c8db5]" />
          </div>
        ) : (
          <>
            <div className="card-elevated p-3">
              <ChartPrice ticker={ticker} />
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card-elevated p-3">
                <ChartShort ticker={ticker} />
              </div>
              <div className="card-elevated p-3">
                <ChartDarkPool ticker={ticker} />
              </div>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="card-elevated p-3">
                <ChartOptions ticker={ticker} />
              </div>
              <div className="card-elevated p-3">
                <GaugeSentiment ticker={ticker} />
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

// ── Parse markdown for chart placeholders ──────────────────────────────

interface TextSegment { type: "text"; html: string }
interface ChartSegment { type: "chart"; chartId: string }
type Segment = TextSegment | ChartSegment;

function parseMarkdown(md: string): Segment[] {
  const segments: Segment[] = [];
  const chartRegex = /!\[chart:(.+?)\]/g;
  let lastIndex = 0;
  let match;

  while ((match = chartRegex.exec(md)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: "text", html: renderText(md.slice(lastIndex, match.index)) });
    }
    segments.push({ type: "chart", chartId: match[1] });
    lastIndex = chartRegex.lastIndex;
  }
  if (lastIndex < md.length) {
    segments.push({ type: "text", html: renderText(md.slice(lastIndex)) });
  }
  if (segments.length === 0) {
    segments.push({ type: "text", html: renderText(md) });
  }
  return segments;
}

function renderText(text: string): string {
  let html = text
    .replace(/^### (.+)$/gm, "<h3>$1</h3>")
    .replace(/^## (.+)$/gm, "<h2>$1</h2>")
    .replace(/^# (.+)$/gm, "<h1>$1</h1>")
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/`(.+?)`/g, "<code>$1</code>")
    .replace(/^---$/gm, "<hr>")
    .split("\n")
    .map((line) => {
      const t = line.trim();
      if (!t) return "";
      if (t.startsWith("<h") || t.startsWith("<code") || t.startsWith("<hr") || t.startsWith("</")) return t;
      if (t.startsWith("- ")) return `<li>${t.slice(2)}</li>`;
      if (t.startsWith("1. ")) return `<li>${t.slice(3)}</li>`;
      return `<p>${t}</p>`;
    })
    .join("\n");
  return html;
}

function renderChart(chartId: string, ticker: string) {
  switch (chartId) {
    case "chart-price": return <ChartPrice ticker={ticker} />;
    case "chart-short": return <ChartShort ticker={ticker} />;
    case "chart-darkpool": return <ChartDarkPool ticker={ticker} />;
    case "chart-options": return <ChartOptions ticker={ticker} />;
    case "gauge-sentiment": return <GaugeSentiment ticker={ticker} />;
    default: return <div className="text-xs text-[#4a5568] text-center py-4">未知图表: {chartId}</div>;
  }
}
