# Clawby Stock Report Generator

> AI-powered US equity analysis reports — backed by [Clawby](https://www.openclawby.com/) real-time financial data.

[![CI](https://github.com/your-username/stock-report/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/stock-report/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/your-username/stock-report/pulls)

> [中文文档](README.zh-CN.md)

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
| 📊 | **Multi-dimensional data** | Quotes, OHLC bars, short data, dark pool, options chain, SEC filings, social sentiment, corporate actions |
| 🤖 | **Multi-LLM support** | OpenAI / Anthropic / any OpenAI-compatible endpoint (DeepSeek, Ollama, Azure, Groq) — add and switch in the UI |
| 📝 | **Customizable report templates** | 4 built-in templates + copy and customize your own prompts & sections |
| 🎨 | **Interactive charts** | 5 Recharts visualizations — price action, short trends, dark pool, options chain, sentiment |
| 📄 | **PDF export** | Print-ready A4 report with cover page, professional typography, page numbers |
| 🔧 | **No database** | All data fetched in real-time from Clawby; zero setup |
| 🐳 | **One-command deploy** | Docker Compose — single command to start everything |

---

## Architecture

```
Browser ──▶ Next.js 14 (Port 3000)
                │
                ▼
          FastAPI (Port 8000)
                │
        ┌───────┴───────┐
        ▼               ▼
   Clawby API        LLM API
   (market data)   (OpenAI/Anthropic)
```

- **Frontend**: Next.js 14, React 18, Tailwind CSS, Recharts, Lucide icons
- **Backend**: Python 3.11+, FastAPI, httpx, Jinja2, WeasyPrint
- **Data**: Clawby API (real-time financial data)
- **LLM**: OpenAI API / Anthropic API / any compatible endpoint
- **Deploy**: Docker Compose

---

## How It Works

1. **Enter a ticker** (e.g., AAPL, MSFT, TSLA) and click "Generate"
2. **Backend fetches all dimensions** from Clawby in parallel (8+ concurrent API calls)
3. **Data is assembled** into a structured context using Jinja2 prompt templates
4. **LLM generates** the analysis report via SSE streaming
5. **Report is rendered** with interactive charts, key metrics, and full Markdown
6. **Export** as Markdown or professional PDF

---

## Configuration

All settings via `.env`:

| Variable | Required | Default | Description |
|---|---|---|---|
| `CLAWBY_API_KEY` | ✅ | — | [Clawby](https://www.openclawby.com/) API key (free) |
| `LLM_API_KEY` | ✅ | — | OpenAI / Anthropic API key |
| `LLM_PROVIDER_TYPE` | ❌ | `openai` | Provider type (`openai` / `anthropic` / `custom_openai`) |
| `LLM_MODEL` | ❌ | `gpt-4o` | Default model name |
| `BACKEND_PORT` | ❌ | `8000` | Backend port |
| `FRONTEND_PORT` | ❌ | `3000` | Frontend port |

Additional LLM providers can be added at runtime via **Settings → LLM Providers**.

---

## Project Structure

```
stock-report/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI entry point
│   │   ├── config.py            # Configuration management
│   │   ├── routers/             # API routes (health, data, report, providers, templates)
│   │   ├── services/            # Clawby client, LLM bridge, demo data, PDF export
│   │   ├── models/              # Pydantic schemas
│   │   ├── presets/             # Built-in templates
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
├── AGENT_SETUP.md               # AI agent installation guide (for Codex, Claude Code, etc.)
├── DEVELOPMENT.md               # Full development documentation (in Chinese)
├── README.zh-CN.md              # Chinese documentation
└── setup.sh                     # One-click setup script
```

---

## AI Agent Setup

This project is designed to be deployed by AI coding agents (Codex, Claude Code, etc.). Just give your agent the repository URL and it will follow the instructions in [`AGENT_SETUP.md`](AGENT_SETUP.md) automatically.

The agent will:
1. Clone the repo
2. Ask you for your API keys
3. Start the services with Docker Compose
4. Open the browser

---

## Development

See [`DEVELOPMENT.md`](DEVELOPMENT.md) (in Chinese) for the complete development plan, API reference, and implementation details.

---

## License

MIT — see [LICENSE](LICENSE).

---

*Not investment advice. Data sourced from Clawby. For informational purposes only.*
