/** Frontend API client — talks to the FastAPI backend. */

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

// ── Helpers ───────────────────────────────────────────────────────────────

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function post<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function put<T>(path: string, body?: unknown): Promise<T> {
  const res = await fetch(`${API}${path}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

async function del<T>(path: string): Promise<T> {
  const res = await fetch(`${API}${path}`, { method: "DELETE" });
  if (!res.ok) {
    const b = await res.json().catch(() => ({}));
    throw new Error(b.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// ── Exports ───────────────────────────────────────────────────────────────

export const api = {
  // Health
  health: () => get<import("@/types").HealthResponse>("/api/health"),

  // Clawby Config
  clawbyConfig: () => get<{configured: boolean; api_key_preview: string}>("/api/clawby-config"),
  updateClawbyKey: (api_key: string) =>
    put<{status: string; message: string}>("/api/clawby-config", { api_key }),
  testClawby: () =>
    post<{success: boolean; message: string; latency_ms: number | null}>("/api/clawby-config/test"),

  // Data
  quote: (ticker: string) => get<import("@/types").QuoteResponse>(`/api/quote/${ticker}`),
  bars: (ticker: string) => get<import("@/types").BarsResponse>(`/api/bars/${ticker}`),

  // LLM Providers
  listProviders: () => get<import("@/types").LLMProvider[]>("/api/providers"),
  createProvider: (data: import("@/types").LLMProviderCreate) =>
    post<import("@/types").LLMProvider>("/api/providers", data),
  updateProvider: (id: string, data: import("@/types").LLMProviderUpdate) =>
    put<import("@/types").LLMProvider>(`/api/providers/${id}`, data),
  deleteProvider: (id: string) => del<{ status: string }>(`/api/providers/${id}`),
  setDefaultProvider: (id: string) =>
    put<{ status: string }>(`/api/providers/default/${id}`),
  testProvider: (id: string) =>
    post<import("@/types").ProviderTestResult>(`/api/providers/${id}/test`),

  // Templates
  listTemplates: () => get<import("@/types").ReportTemplate[]>("/api/templates"),
  createTemplate: (data: import("@/types").ReportTemplateCreate) =>
    post<import("@/types").ReportTemplate>("/api/templates", data),
  copyTemplate: (id: string) =>
    post<import("@/types").ReportTemplate>(`/api/templates/${id}/copy`),
  updateTemplate: (id: string, data: Partial<import("@/types").ReportTemplateCreate>) =>
    put<import("@/types").ReportTemplate>(`/api/templates/${id}`, data),
  deleteTemplate: (id: string) => del<{ status: string }>(`/api/templates/${id}`),

  // Reports
  submitReport: (req: import("@/types").ReportRequest) => req,
  getReport: (id: string) => get<Record<string, unknown>>(`/api/report/${id}`),
  listReports: () => get<import("@/types").ReportListItem[]>("/api/report-history"),
};

// ── SSE report stream ─────────────────────────────────────────────────────

export function streamReport(
  req: import("@/types").ReportRequest,
  onProgress: (evt: import("@/types").ProgressEvent) => void,
  onChunk: (evt: import("@/types").ChunkEvent) => void,
  onComplete: (evt: import("@/types").CompleteEvent) => void,
  onError: (evt: import("@/types").ErrorEvent) => void,
): AbortController {
  const controller = new AbortController();

  fetch(`${API}/api/report`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
    signal: controller.signal,
  })
    .then(async (response) => {
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        onError({ code: "http_error", message: body.detail || `HTTP ${response.status}` });
        return;
      }

      const reader = response.body?.getReader();
      if (!reader) {
        onError({ code: "no_stream", message: "Response body is not readable" });
        return;
      }

      const decoder = new TextDecoder();
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        let currentEvent = "";
        for (const line of lines) {
          if (line.startsWith("event: ")) {
            currentEvent = line.slice(7).trim();
          } else if (line.startsWith("data: ")) {
            const dataStr = line.slice(6);
            try {
              const data = JSON.parse(dataStr);
              switch (currentEvent) {
                case "progress":
                  onProgress(data as import("@/types").ProgressEvent);
                  break;
                case "chunk":
                  onChunk(data as import("@/types").ChunkEvent);
                  break;
                case "complete":
                  onComplete(data as import("@/types").CompleteEvent);
                  break;
                case "error":
                  onError(data as import("@/types").ErrorEvent);
                  break;
              }
            } catch {
              // ignore malformed JSON
            }
          }
        }
      }
    })
    .catch((err) => {
      if (err.name !== "AbortError") {
        onError({ code: "fetch_error", message: err.message });
      }
    });

  return controller;
}
