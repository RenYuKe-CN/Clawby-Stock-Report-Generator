# Clawby Stock Report Generator

> AI-powered US equity analysis reports — powered by [Clawby](https://www.openclawby.com/) real-time financial data.

[![CI](https://github.com/your-username/stock-report/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/stock-report/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/your-username/stock-report/pulls)

---

## Quick Start

```bash
# 1. Clone
git clone <repository-url>
cd stock-report

# 2. Configure
cp .env.example .env
# Edit .env → fill in CLAWBY_API_KEY and LLM_API_KEY

# 3. Launch with Docker
bash setup.sh

# 4. Open
open http://localhost:3000
```

**Prerequisites:** Docker & Docker Compose, [Clawby API Key](https://www.openclawby.com/) (free), LLM API Key (OpenAI / Anthropic).

---

## Features

| | Feature | Description |
|---|---|---|
| 📊 | **Multi-dimensional data** | Quotes, OHLC bars, short data, dark pool, options chain, SEC financials, Reddit sentiment, corporate actions |
| 🤖 | **Multi-LLM support** | OpenAI / Anthropic / OpenAI-compatible (DeepSeek, Ollama, Azure, Groq) — add and switch in UI |
| 📝 | **Customizable templates** | 4 built-in templates + copy and edit your own |
| 🎨 | **Professional charts** | 5 Recharts visualizations (price, short, dark pool, options, sentiment) |
| 📄 | **PDF export** | Print-ready A4 PDF with cover page, professional styling, page numbers |
| 🔧 | **Zero database** | All data fetched in real-time from Clawby; no database setup required |
| 🐳 | **One-click deploy** | Docker Compose — single command to start everything |

---

## Architecture

```
┌──────────┐     ┌──────────────┐     ┌────────────┐
│  Browser  │────▶│  Next.js 14  │────▶│  FastAPI   │
│          │     │  (Port 3000) │     │ (Port 8000)│
│  Charts  │     │  Tailwind    │     │  httpx     │
│ Recharts │     │  Lucide Icons│     │  WeasyPrint│
└──────────┘     └──────────────┘     └────────────┘
                                            │
                                    ┌───────▼────────┐
                                    │   Clawby API   │
                                    │  Real-time data │
                                    └────────────────┘
                                    ┌───────▼────────┐
                                    │   LLM API      │
                                    │ OpenAI/Anthropic│
                                    └────────────────┘
```

---

## Screenshots

> *Report generation page — input ticker, select template & LLM, stream report in real-time*

```
┌──────────────────────────────────────────────────┐
│  Clawby Report                       OpenAI ✅   │
├──────────────────────────────────────────────────┤
│  [AAPL]          [生成报告]                        │
│  模板: 全面分析  LLM: GPT-4o  模型: gpt-4o        │
├──────────────────────────────────────────────────┤
│  ## AAPL 综合分析报告                              │
│  Apple Inc. 当前股价 $245.67...                    │
│  [📈 价格走势图]  [📊 做空趋势]  [📉 期权链]      │
└──────────────────────────────────────────────────┘
```

---

## How It Works

1. **User enters a ticker** (e.g., AAPL, MSFT, TSLA) and clicks "Generate"
2. **Backend fetches all data dimensions** from Clawby API in parallel (8+ concurrent calls)
3. **Data is assembled** into a structured context with Jinja2 prompt templates
4. **LLM generates** the analysis report via streaming SSE
5. **Report is rendered** with interactive charts, markdown, and key metrics
6. **Export** as Markdown or professional PDF

---

## Project Structure

```
stock-report/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry
│   │   ├── config.py            # Configuration management
│   │   ├── routers/             # API routes (health, data, report, providers, templates)
│   │   ├── services/            # Clawby client, LLM bridge, demo data, PDF export
│   │   ├── models/              # Pydantic schemas
│   │   ├── presets/             # Built-in templates & provider defaults
│   │   └── templates/           # Jinja2 prompt templates
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js pages (home, report, settings, history)
│   │   ├── components/          # React components (charts, layout, report viewer)
│   │   ├── lib/                 # API client + SSE streaming
│   │   └── types/               # TypeScript definitions
│   └── Dockerfile
├── docker-compose.yml           # One-command deployment
├── AGENT_SETUP.md               # AI agent installation guide
├── DEVELOPMENT.md               # Full development documentation
└── setup.sh                     # One-click setup script
```

---

## Configuration

All settings via `.env`:

| Variable | Required | Description |
|---|---|---|
| `CLAWBY_API_KEY` | ✅ | [Clawby](https://www.openclawby.com/) API key (free) |
| `LLM_API_KEY` | ✅ | OpenAI / Anthropic API key |
| `LLM_PROVIDER_TYPE` | ❌ | `openai` / `anthropic` / `custom_openai` |
| `LLM_MODEL` | ❌ | Model name (default: `gpt-4o`) |
| `BACKEND_PORT` | ❌ | Backend port (default: `8000`) |
| `FRONTEND_PORT` | ❌ | Frontend port (default: `3000`) |

Additional providers can be added via the **Settings → LLM Providers** page at runtime.

---

## Development

See [DEVELOPMENT.md](DEVELOPMENT.md) for the full development plan, API reference, and implementation details.

---

## License

MIT — see [LICENSE](LICENSE).

---

*Not investment advice. Data sourced from Clawby. This tool is for informational purposes only.*

---

*[English](README.md) | 中文*
