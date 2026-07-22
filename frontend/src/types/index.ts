/** Shared TypeScript types for the frontend. */

// ── Health ────────────────────────────────────────────────────────────────

export interface HealthResponse {
  status: string;
  clawby_configured: boolean;
  clawby_status: string;
  providers_count: number;
  default_provider: string | null;
}

// ── LLM Provider ──────────────────────────────────────────────────────────

export type ProviderType = "openai" | "anthropic" | "custom_openai" | "custom_anthropic";

export interface LLMProvider {
  id: string;
  name: string;
  provider_type: ProviderType;
  api_base: string;
  api_key: string;
  default_model: string;
  supported_models: string[];
  max_tokens: number;
  supports_streaming: boolean;
  is_default: boolean;
  is_available: boolean;
  last_tested_at: string | null;
  error_message: string | null;
  created_at: string;
  updated_at: string;
}

export interface LLMProviderCreate {
  name: string;
  provider_type: ProviderType;
  api_base: string;
  api_key: string;
  default_model: string;
  supported_models?: string[];
  max_tokens?: number;
  supports_streaming?: boolean;
}

export interface LLMProviderUpdate {
  name?: string;
  api_base?: string;
  api_key?: string;
  default_model?: string;
  supported_models?: string[];
  max_tokens?: number;
  supports_streaming?: boolean;
}

export interface ProviderTestResult {
  success: boolean;
  message: string;
  latency_ms: number | null;
}

// ── Report Templates ──────────────────────────────────────────────────────

export interface SectionDef {
  id: string;
  title: Record<string, string>;
  order: number;
  required: boolean;
  data_dependencies: string[];
  chart_hints: string[];
  max_length?: number;
}

export type Language = "zh-CN" | "en";

export interface ReportTemplate {
  id: string;
  name: string;
  description: string;
  category: "builtin" | "custom";
  sections: SectionDef[];
  system_prompt: string;
  user_prompt_template: string;
  required_data: string[];
  optional_data: string[];
  language: Language[];
  output_format: string;
  default_model?: string;
  pdf_css_template?: string;
  pdf_margin_top?: string;
  pdf_margin_bottom?: string;
  created_at: string;
  updated_at: string;
  version: number;
}

export interface ReportTemplateCreate {
  name: string;
  description?: string;
  sections: SectionDef[];
  system_prompt: string;
  user_prompt_template: string;
  required_data: string[];
  optional_data?: string[];
  language?: Language[];
  output_format?: string;
  default_model?: string;
  pdf_margin_top?: string;
  pdf_margin_bottom?: string;
}

// ── Report Generation ─────────────────────────────────────────────────────

export interface ReportRequest {
  ticker: string;
  template_id: string;
  provider_id?: string;
  model?: string;
  language: Language;
}

export interface ProgressEvent {
  step: string;
  message: string;
  progress: number;
}

export interface ChunkEvent {
  text: string;
}

export interface CompleteEvent {
  id: string;
  markdown: string;
  template_id: string;
  provider_name: string;
  model: string;
  generated_at: string;
}

export interface ErrorEvent {
  code: string;
  message: string;
}

export interface ReportListItem {
  id: string;
  ticker: string;
  template_name: string;
  provider_name: string;
  model: string;
  generated_at: string;
  language: Language;
}

// ── Data endpoints ────────────────────────────────────────────────────────

export interface QuoteResponse {
  ticker: string;
  price: number | null;
  change: number | null;
  change_pct: number | null;
  market_cap: number | null;
  volume: number | null;
  raw?: Record<string, unknown>;
}

export interface BarsResponse {
  ticker: string;
  bars: Array<Record<string, unknown>>;
  count: number;
}
