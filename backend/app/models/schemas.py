"""Pydantic v2 request / response models."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


# ── Enums / Literals ────────────────────────────────────────────────────────

TickerStr = Field(
    ..., min_length=1, max_length=5, pattern=r"^[A-Z]{1,5}$",
    description="US stock ticker symbol, e.g. AAPL",
)

ProviderType = Literal["openai", "anthropic", "custom_openai", "custom_anthropic"]

Language = Literal["zh-CN", "en"]

ReportStep = Literal[
    "validating",
    "fetching_quote",
    "fetching_bars",
    "fetching_short",
    "fetching_darkpool",
    "fetching_options",
    "fetching_financials",
    "fetching_sentiment",
    "fetching_corporate",
    "generating",
    "done",
]


# ── Health ──────────────────────────────────────────────────────────────────

class HealthResponse(BaseModel):
    status: str = "ok"
    clawby_configured: bool = False
    clawby_status: str = "unknown"       # ok | invalid_key | error
    providers_count: int = 0
    default_provider: str | None = None


# ── Data endpoints ──────────────────────────────────────────────────────────

class QuoteResponse(BaseModel):
    ticker: str
    price: float | None = None
    change: float | None = None
    change_pct: float | None = None
    market_cap: float | None = None
    volume: int | None = None
    source: str = "clawby"
    raw: dict[str, Any] | None = None


class BarsResponse(BaseModel):
    ticker: str
    bars: list[dict[str, Any]] = []
    count: int = 0


class ShortDataResponse(BaseModel):
    ticker: str
    short_volume: list[dict[str, Any]] = []
    short_interest: list[dict[str, Any]] = []
    daily_short_interest: list[dict[str, Any]] = []
    borrow_fee: list[dict[str, Any]] = []
    ftds: list[dict[str, Any]] = []


class DarkPoolResponse(BaseModel):
    ticker: str
    date: str | None = None
    levels: list[dict[str, Any]] = []
    summary: dict[str, Any] = {}


class OptionsResponse(BaseModel):
    ticker: str
    underlying: str
    expiration: str | None = None
    max_pain: float | None = None
    chain: list[dict[str, Any]] = []


class FinancialsResponse(BaseModel):
    ticker: str
    company_name: str | None = None
    revenue: list[dict[str, Any]] = []
    net_income: list[dict[str, Any]] = []
    eps: list[dict[str, Any]] = []
    assets: list[dict[str, Any]] = []
    equity: list[dict[str, Any]] = []


class CorporateActionsResponse(BaseModel):
    ticker: str
    dividends: list[dict[str, Any]] = []
    splits: list[dict[str, Any]] = []
    float_history: list[dict[str, Any]] = []


class SentimentResponse(BaseModel):
    ticker: str
    mentions: list[dict[str, Any]] = []
    daily_counts: list[dict[str, Any]] = []


# ── Report ──────────────────────────────────────────────────────────────────

class ReportRequest(BaseModel):
    ticker: str = TickerStr
    template_id: str = "rpt_comprehensive"
    provider_id: str | None = None          # None → use default
    model: str | None = None                # None → use provider's default_model
    language: Language = "zh-CN"


class ProgressEvent(BaseModel):
    step: ReportStep
    message: str
    progress: int = 0                       # 0–100 percentage


class ChunkEvent(BaseModel):
    text: str


class CompleteEvent(BaseModel):
    id: str
    markdown: str
    template_id: str
    provider_name: str
    model: str
    generated_at: str


class ErrorEvent(BaseModel):
    code: str
    message: str


class ReportListItem(BaseModel):
    id: str
    ticker: str
    template_name: str
    provider_name: str
    model: str
    generated_at: datetime
    language: Language


class ReportDetail(BaseModel):
    id: str
    ticker: str
    template_id: str
    provider_id: str
    model: str
    language: Language
    markdown: str
    generated_at: datetime


# ── LLM Provider ────────────────────────────────────────────────────────────

class LLMProviderBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=64)
    provider_type: ProviderType
    api_base: str
    api_key: str = ""
    default_model: str
    supported_models: list[str] = []
    max_tokens: int = 8192
    supports_streaming: bool = True


class LLMProviderCreate(LLMProviderBase):
    pass


class LLMProviderUpdate(BaseModel):
    name: str | None = None
    api_base: str | None = None
    api_key: str | None = None
    default_model: str | None = None
    supported_models: list[str] | None = None
    max_tokens: int | None = None
    supports_streaming: bool | None = None


class LLMProviderResponse(LLMProviderBase):
    id: str
    is_default: bool = False
    is_available: bool = False
    last_tested_at: datetime | None = None
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ProviderTestResult(BaseModel):
    success: bool
    message: str
    latency_ms: int | None = None


# ── Report Templates ────────────────────────────────────────────────────────

class SectionDef(BaseModel):
    id: str
    title: dict[Language, str]
    order: int
    required: bool = True
    data_dependencies: list[str] = []
    chart_hints: list[str] = []
    max_length: int | None = None


class ReportTemplateBase(BaseModel):
    name: str
    description: str = ""
    sections: list[SectionDef] = []
    system_prompt: str = ""
    user_prompt_template: str = ""
    required_data: list[str] = []
    optional_data: list[str] = []
    language: list[Language] = ["zh-CN", "en"]
    output_format: str = "markdown"
    default_model: str | None = None
    pdf_css_template: str | None = None
    pdf_margin_top: str = "14mm"
    pdf_margin_bottom: str = "16mm"


class ReportTemplateCreate(ReportTemplateBase):
    pass


class ReportTemplateUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    sections: list[SectionDef] | None = None
    system_prompt: str | None = None
    user_prompt_template: str | None = None
    required_data: list[str] | None = None
    optional_data: list[str] | None = None
    language: list[Language] | None = None
    output_format: str | None = None
    default_model: str | None = None
    pdf_css_template: str | None = None
    pdf_margin_top: str | None = None
    pdf_margin_bottom: str | None = None


class ReportTemplateResponse(ReportTemplateBase):
    id: str
    category: str = "custom"           # "builtin" | "custom"
    created_at: datetime
    updated_at: datetime
    version: int = 1


# ── Error ───────────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    detail: str
