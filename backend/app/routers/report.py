"""Report generation router — SSE streaming + CRUD for providers & templates."""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response, StreamingResponse
from jinja2 import Template

from pathlib import Path
from app.config import load_json, save_json, settings
from app.models.schemas import (
    LLMProviderCreate,
    LLMProviderUpdate,
    LLMProviderResponse,
    ProviderTestResult,
    ReportDetail,
    ReportListItem,
    ReportRequest,
    ReportTemplateCreate,
    ReportTemplateResponse,
    ReportTemplateUpdate,
)
from app.services import clawby
from app.services.llm import generate_stream, registry, test_provider, update_provider_status

router = APIRouter(tags=["report"])


# ═══════════════════════════════════════════════════════════════════════════
#  Report Generation
# ═══════════════════════════════════════════════════════════════════════════

def _load_templates() -> list[dict[str, Any]]:
    """Load templates from the data file, falling back to presets."""
    data = load_json(settings.templates_path)
    if not data:
        # Seed with presets
        import importlib.resources as res
        try:
            from app.presets import templates as presets_module
            with res.files(presets_module).joinpath("../../../presets/templates.json").open() as f:
                data = json.load(f)
        except (ImportError, FileNotFoundError):
            pass
        if not data:
            data = []
        save_json(settings.templates_path, data)
    return data


def _save_templates(data: list[dict[str, Any]]) -> None:
    save_json(settings.templates_path, data)


@router.post("/api/report")
async def generate_report(req: ReportRequest):
    """Generate a report via SSE streaming."""

    ticker = req.ticker.upper()

    # ── Resolve template ───────────────────────────────────────────────
    templates = _load_templates()
    tmpl_def = next((t for t in templates if t["id"] == req.template_id), None)
    if not tmpl_def:
        raise HTTPException(404, f"Template '{req.template_id}' not found")

    # ── Resolve provider ───────────────────────────────────────────────
    provider_id = req.provider_id or registry.default_id
    if not provider_id:
        raise HTTPException(400, "No LLM provider configured and no default set")
    provider = registry.get(provider_id)
    if not provider:
        raise HTTPException(404, f"Provider '{provider_id}' not found")

    model = req.model or provider.get("default_model", "gpt-4o")

    # ── Helper: yield SSE events ───────────────────────────────────────
    async def _progress(step: str, message: str, progress: int = 0):
        return f"event: progress\ndata: {json.dumps({'step': step, 'message': message, 'progress': progress})}\n\n"

    async def _chunk(text: str):
        return f"event: chunk\ndata: {json.dumps({'text': text})}\n\n"

    async def _error(code: str, message: str):
        return f"event: error\ndata: {json.dumps({'code': code, 'message': message})}\n\n"

    async def _complete(report_id: str, markdown: str):
        payload = {
            'id': report_id,
            'markdown': markdown,
            'template_id': tmpl_def['id'],
            'provider_name': provider['name'],
            'model': model,
            'generated_at': datetime.now(timezone.utc).isoformat(),
        }
        data_str = json.dumps(payload)
        return f"event: complete\ndata: {data_str}\n\n"

    # ── SSE streaming generator ────────────────────────────────────────
    async def event_stream():
        yield await _progress("validating", f"正在验证股票代码 {ticker}...", 5)

        # ── Parallel data fetch ─────────────────────────────────────────
        required = tmpl_def.get("required_data", [])
        optional = tmpl_def.get("optional_data", [])

        fetch_steps = {
            "quote": ("fetching_quote", "拉取行情数据...", 15),
            "bars": ("fetching_bars", "拉取日线走势...", 22),
            "short": ("fetching_short", "拉取做空数据...", 30),
            "darkpool": ("fetching_darkpool", "拉取暗池数据...", 38),
            "options": ("fetching_options", "拉取期权链...", 45),
            "financials": ("fetching_financials", "拉取财务基本面...", 55),
            "sentiment": ("fetching_sentiment", "拉取市场情绪...", 62),
            "corporate": ("fetching_corporate", "拉取公司行动...", 68),
        }

        import asyncio

        fetchers = {
            "quote": clawby.get_quote,
            "bars": clawby.get_bars,
            "short": clawby.get_short_all,
            "darkpool": clawby.get_darkpool,
            "options": clawby.get_options_chain,
            "financials": clawby.get_financials,
            "sentiment": clawby.get_sentiment,
            "corporate": clawby.get_corporate,
        }

        data_bundle: dict[str, Any] = {}

        # Fire all required + optional fetches concurrently
        all_dims = set(required) | set(optional)
        tasks = {}
        for dim in all_dims:
            if dim in fetchers:
                tasks[dim] = asyncio.create_task(fetchers[dim](ticker))

        # Yield progress as each completes
        for dim, task in tasks.items():
            step, msg, pct = fetch_steps.get(dim, ("fetching_data", f"拉取 {dim} 数据...", 10))
            yield await _progress(step, msg, pct)
            try:
                result = await task
                data_bundle[dim] = result
            except Exception as e:
                data_bundle[dim] = {"error": str(e), "data": None}
                yield await _progress(step, f"{msg} 失败: {str(e)[:60]}", pct)

        yield await _progress("generating", "AI 正在撰写分析报告...", 75)

        # ── Render prompt with Jinja2 ───────────────────────────────────
        lang = req.language
        lang_name = "中文" if lang == "zh-CN" else "English"

        import json as _json

        def _fmt(data: Any) -> str:
            """Format data for prompt insertion."""
            if isinstance(data, dict) and "error" in data:
                return f"Data unavailable: {data['error']}"
            return _json.dumps(data, indent=2, ensure_ascii=False, default=str)[:8000]

        context = {
            "ticker": ticker,
            "language": lang,
            "language_name": lang_name,
            "template_name": tmpl_def["name"],
            "sections": tmpl_def.get("sections", []),
            "generation_time": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "quote_data": _fmt(data_bundle.get("quote", {})),
            "bars_data": _fmt(data_bundle.get("bars", [])),
            "short_data": _fmt(data_bundle.get("short", {})),
            "darkpool_data": _fmt(data_bundle.get("darkpool", {})),
            "options_data": _fmt(data_bundle.get("options", {})),
            "financials_data": _fmt(data_bundle.get("financials", {})),
            "sentiment_data": _fmt(data_bundle.get("sentiment", {})),
            "corporate_data": _fmt(data_bundle.get("corporate", {})),
        }

        try:
            sys_template = Template(tmpl_def.get("system_prompt", ""))
            user_template = Template(tmpl_def.get("user_prompt_template", ""))
            system_prompt = sys_template.render(**context)
            user_prompt = user_template.render(**context)
        except Exception as e:
            yield await _error("template_error", f"Prompt rendering failed: {str(e)}")
            return

        # ── Stream LLM response ────────────────────────────────────────
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        markdown_parts: list[str] = []
        try:
            async for event_type, data_str in generate_stream(provider_id, model, system_prompt, user_prompt):
                if event_type == "chunk":
                    payload = json.loads(data_str)
                    text = payload.get("text", "")
                    markdown_parts.append(text)
                    yield await _chunk(text)
                elif event_type == "error":
                    yield data_str  # Already formatted as "event: error..."
                    return
        except Exception as e:
            yield await _error("generation_error", f"LLM streaming failed: {str(e)}")
            return

        # ── Save report snapshot ───────────────────────────────────────
        full_markdown = "".join(markdown_parts)
        report_id = f"rpt_{uuid.uuid4().hex[:12]}"
        snapshot = {
            "id": report_id,
            "ticker": ticker,
            "template_id": tmpl_def["id"],
            "template_name": tmpl_def["name"],
            "provider_id": provider_id,
            "provider_name": provider["name"],
            "model": model,
            "language": lang,
            "markdown": full_markdown,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
        history = load_json(Path(settings.data_dir) / "report_history.json")
        history.insert(0, snapshot)
        history = history[:100]  # Keep last 100
        save_json(Path(settings.data_dir) / "report_history.json", history)

        yield await _complete(report_id, full_markdown)

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "X-Accel-Buffering": "no",
            "Access-Control-Allow-Origin": "*",
        },
    )


@router.get("/api/report/{report_id}")
async def get_report(report_id: str):
    history = load_json(Path(settings.data_dir) / "report_history.json")
    entry = next((r for r in history if r["id"] == report_id), None)
    if not entry:
        raise HTTPException(404, "Report not found")
    return entry


@router.get("/api/report-history", response_model=list[ReportListItem])
async def list_reports():
    history = load_json(Path(settings.data_dir) / "report_history.json")
    items = []
    for r in history[:50]:
        items.append(ReportListItem(
            id=r["id"],
            ticker=r.get("ticker", ""),
            template_name=r.get("template_name", ""),
            provider_name=r.get("provider_name", ""),
            model=r.get("model", ""),
            generated_at=datetime.fromisoformat(r["generated_at"]),
            language=r.get("language", "zh-CN"),
        ))
    return items


# ═══════════════════════════════════════════════════════════════════════════
#  LLM Provider CRUD
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/api/providers", response_model=list[LLMProviderResponse])
async def list_providers():
    return [
        LLMProviderResponse(
            id=p["id"],
            name=p["name"],
            provider_type=p["provider_type"],
            api_base=p["api_base"],
            api_key="***" if p.get("api_key") else "",
            default_model=p["default_model"],
            supported_models=p.get("supported_models", []),
            max_tokens=p.get("max_tokens", 8192),
            supports_streaming=p.get("supports_streaming", True),
            is_default=p.get("is_default", False),
            is_available=p.get("is_available", False),
            last_tested_at=datetime.fromisoformat(p["last_tested_at"]) if p.get("last_tested_at") else None,
            error_message=p.get("error_message"),
            created_at=datetime.fromisoformat(p["created_at"]),
            updated_at=datetime.fromisoformat(p["updated_at"]),
        )
        for p in registry.list()
    ]


@router.post("/api/providers", response_model=LLMProviderResponse)
async def create_provider(data: LLMProviderCreate):
    entry = registry.create(data.model_dump())
    return LLMProviderResponse(
        id=entry["id"],
        name=entry["name"],
        provider_type=entry["provider_type"],
        api_base=entry["api_base"],
        api_key="***" if entry.get("api_key") else "",
        default_model=entry["default_model"],
        supported_models=entry.get("supported_models", []),
        max_tokens=entry.get("max_tokens", 8192),
        supports_streaming=entry.get("supports_streaming", True),
        is_default=entry.get("is_default", False),
        is_available=entry.get("is_available", False),
        created_at=datetime.fromisoformat(entry["created_at"]),
        updated_at=datetime.fromisoformat(entry["updated_at"]),
    )


@router.put("/api/providers/{pid}", response_model=LLMProviderResponse)
async def update_provider(pid: str, data: LLMProviderUpdate):
    entry = registry.update(pid, data.model_dump(exclude_none=True))
    if not entry:
        raise HTTPException(404, "Provider not found")
    return LLMProviderResponse(
        id=entry["id"],
        name=entry["name"],
        provider_type=entry["provider_type"],
        api_base=entry["api_base"],
        api_key="***" if entry.get("api_key") else "",
        default_model=entry["default_model"],
        supported_models=entry.get("supported_models", []),
        max_tokens=entry.get("max_tokens", 8192),
        supports_streaming=entry.get("supports_streaming", True),
        is_default=entry.get("is_default", False),
        is_available=entry.get("is_available", False),
        last_tested_at=datetime.fromisoformat(entry["last_tested_at"]) if entry.get("last_tested_at") else None,
        error_message=entry.get("error_message"),
        created_at=datetime.fromisoformat(entry["created_at"]),
        updated_at=datetime.fromisoformat(entry["updated_at"]),
    )


@router.delete("/api/providers/{pid}")
async def delete_provider(pid: str):
    ok = registry.delete(pid)
    if not ok:
        raise HTTPException(404, "Provider not found")
    return {"status": "deleted"}


@router.put("/api/providers/default/{pid}")
async def set_default_provider(pid: str):
    ok = registry.set_default(pid)
    if not ok:
        raise HTTPException(404, "Provider not found")
    return {"status": "default_updated"}


@router.post("/api/providers/{pid}/test", response_model=ProviderTestResult)
async def test_provider_route(pid: str):
    result = await test_provider(pid)
    await update_provider_status(pid, result)
    return ProviderTestResult(**result)


# ═══════════════════════════════════════════════════════════════════════════
#  Report Template CRUD
# ═══════════════════════════════════════════════════════════════════════════

@router.get("/api/templates", response_model=list[ReportTemplateResponse])
async def list_templates():
    templates = _load_templates()
    return [
        ReportTemplateResponse(
            id=t["id"],
            name=t["name"],
            description=t.get("description", ""),
            category=t.get("category", "custom"),
            sections=t.get("sections", []),
            system_prompt=t.get("system_prompt", ""),
            user_prompt_template=t.get("user_prompt_template", ""),
            required_data=t.get("required_data", []),
            optional_data=t.get("optional_data", []),
            language=t.get("language", ["zh-CN", "en"]),
            output_format=t.get("output_format", "markdown"),
            default_model=t.get("default_model"),
            pdf_css_template=t.get("pdf_css_template"),
            pdf_margin_top=t.get("pdf_margin_top", "14mm"),
            pdf_margin_bottom=t.get("pdf_margin_bottom", "16mm"),
            created_at=datetime.fromisoformat(t.get("created_at", datetime.now(timezone.utc).isoformat())),
            updated_at=datetime.fromisoformat(t.get("updated_at", datetime.now(timezone.utc).isoformat())),
            version=t.get("version", 1),
        )
        for t in templates
    ]


@router.post("/api/templates", response_model=ReportTemplateResponse)
async def create_template(data: ReportTemplateCreate):
    templates = _load_templates()
    import uuid
    now = datetime.now(timezone.utc).isoformat()
    entry = {
        "id": f"rpt_{uuid.uuid4().hex[:12]}",
        "category": "custom",
        "created_at": now,
        "updated_at": now,
        "version": 1,
        **data.model_dump(),
    }
    templates.append(entry)
    _save_templates(templates)
    return ReportTemplateResponse(
        id=entry["id"],
        name=entry["name"],
        description=entry.get("description", ""),
        category="custom",
        sections=entry.get("sections", []),
        system_prompt=entry.get("system_prompt", ""),
        user_prompt_template=entry.get("user_prompt_template", ""),
        required_data=entry.get("required_data", []),
        optional_data=entry.get("optional_data", []),
        language=entry.get("language", ["zh-CN", "en"]),
        output_format=entry.get("output_format", "markdown"),
        default_model=entry.get("default_model"),
        pdf_css_template=entry.get("pdf_css_template"),
        pdf_margin_top=entry.get("pdf_margin_top", "14mm"),
        pdf_margin_bottom=entry.get("pdf_margin_bottom", "16mm"),
        created_at=datetime.fromisoformat(entry["created_at"]),
        updated_at=datetime.fromisoformat(entry["updated_at"]),
        version=entry.get("version", 1),
    )


@router.put("/api/templates/{tid}", response_model=ReportTemplateResponse)
async def update_template(tid: str, data: ReportTemplateUpdate):
    templates = _load_templates()
    idx = next((i for i, t in enumerate(templates) if t["id"] == tid), None)
    if idx is None:
        raise HTTPException(404, "Template not found")
    if templates[idx].get("category") == "builtin":
        raise HTTPException(403, "Built-in templates cannot be modified; copy them instead")

    updates = data.model_dump(exclude_none=True)
    templates[idx].update(updates)
    templates[idx]["updated_at"] = datetime.now(timezone.utc).isoformat()
    templates[idx]["version"] = templates[idx].get("version", 1) + 1
    _save_templates(templates)

    t = templates[idx]
    return ReportTemplateResponse(
        id=t["id"], name=t["name"], description=t.get("description", ""),
        category=t.get("category", "custom"),
        sections=t.get("sections", []),
        system_prompt=t.get("system_prompt", ""),
        user_prompt_template=t.get("user_prompt_template", ""),
        required_data=t.get("required_data", []), optional_data=t.get("optional_data", []),
        language=t.get("language", ["zh-CN", "en"]),
        output_format=t.get("output_format", "markdown"),
        default_model=t.get("default_model"),
        pdf_css_template=t.get("pdf_css_template"),
        pdf_margin_top=t.get("pdf_margin_top", "14mm"),
        pdf_margin_bottom=t.get("pdf_margin_bottom", "16mm"),
        created_at=datetime.fromisoformat(t["created_at"]),
        updated_at=datetime.fromisoformat(t["updated_at"]),
        version=t.get("version", 1),
    )


@router.post("/api/templates/{tid}/copy", response_model=ReportTemplateResponse)
async def copy_template(tid: str):
    templates = _load_templates()
    src = next((t for t in templates if t["id"] == tid), None)
    if not src:
        raise HTTPException(404, "Template not found")
    import uuid
    now = datetime.now(timezone.utc).isoformat()
    entry = {**src, "id": f"rpt_{uuid.uuid4().hex[:12]}", "category": "custom",
             "name": f"{src['name']} (副本)", "created_at": now, "updated_at": now, "version": 1}
    templates.append(entry)
    _save_templates(templates)
    return ReportTemplateResponse(
        id=entry["id"], name=entry["name"], description=entry.get("description", ""),
        category="custom", sections=entry.get("sections", []),
        system_prompt=entry.get("system_prompt", ""),
        user_prompt_template=entry.get("user_prompt_template", ""),
        required_data=entry.get("required_data", []), optional_data=entry.get("optional_data", []),
        language=entry.get("language", ["zh-CN", "en"]),
        output_format=entry.get("output_format", "markdown"),
        default_model=entry.get("default_model"),
        pdf_css_template=entry.get("pdf_css_template"),
        pdf_margin_top=entry.get("pdf_margin_top", "14mm"),
        pdf_margin_bottom=entry.get("pdf_margin_bottom", "16mm"),
        created_at=datetime.fromisoformat(entry["created_at"]),
        updated_at=datetime.fromisoformat(entry["updated_at"]),
        version=entry.get("version", 1),
    )


@router.delete("/api/templates/{tid}")
async def delete_template(tid: str):
    templates = _load_templates()
    idx = next((i for i, t in enumerate(templates) if t["id"] == tid), None)
    if idx is None:
        raise HTTPException(404, "Template not found")
    if templates[idx].get("category") == "builtin":
        raise HTTPException(403, "Built-in templates cannot be deleted")
    templates.pop(idx)
    _save_templates(templates)
    return {"status": "deleted"}
@router.get("/api/report/{report_id}/pdf")
async def export_report_pdf(report_id: str):
    """Export a report as PDF via WeasyPrint."""
    from app.services.pdf import generate_pdf
    history = load_json(Path(settings.data_dir) / "report_history.json")
    entry = next((r for r in history if r["id"] == report_id), None)
    if not entry:
        raise HTTPException(404, "Report not found")

    try:
        pdf_bytes = generate_pdf(
            ticker=entry.get("ticker", ""),
            template_name=entry.get("template_name", "Report"),
            provider_name=entry.get("provider_name", "AI"),
            model=entry.get("model", ""),
            generated_at=entry.get("generated_at", ""),
            markdown_body=entry.get("markdown", ""),
        )
    except Exception as e:
        raise HTTPException(500, detail=f"PDF generation failed: {str(e)}")

    from fastapi.responses import Response
    filename = f"{entry.get('ticker', 'report')}_report.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
