# Clawby Stock Report Generator

> AI 驱动的美股分析报告 — 由 [Clawby](https://www.openclawby.com/) 实时金融数据提供支撑。

[![CI](https://github.com/your-username/stock-report/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/stock-report/actions/workflows/ci.yml)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![Next.js 14](https://img.shields.io/badge/Next.js-14-black.svg)](https://nextjs.org/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](https://github.com/your-username/stock-report/pulls)

> [English](README.md)

---

## 快速开始

```bash
# 1. 克隆仓库
git clone <repository-url>
cd stock-report

# 2. 配置环境
cp .env.example .env
# 编辑 .env → 填入 CLAWBY_API_KEY 和 LLM_API_KEY

# 3. 使用 Docker 启动
bash setup.sh

# 4. 打开浏览器
open http://localhost:3000
```

**前置要求：** Docker & Docker Compose、[Clawby API Key](https://www.openclawby.com/)（免费）、LLM API Key（OpenAI / Anthropic）。

---

## 功能特性

| | 功能 | 描述 |
|---|---|---|
| 📊 | **多维度数据** | 实时行情、OHLC K线、做空数据、暗池交易、期权链、SEC 财报、社交情绪、公司事件 |
| 🤖 | **多 LLM 支持** | OpenAI / Anthropic / 任何 OpenAI 兼容端点（DeepSeek、Ollama、Azure、Groq）— 在 UI 中添加和切换 |
| 📝 | **可定制报告模板** | 4 个内置模板 + 复制并自定义你的提示词和章节 |
| 🎨 | **交互式图表** | 5 个 Recharts 可视化 — 价格走势、做空趋势、暗池、期权链、情绪指数 |
| 📄 | **PDF 导出** | 打印就绪的 A4 报告，包含封面、专业排版、页码 |
| 🔧 | **无数据库设计** | 所有数据都从 Clawby 实时获取；零配置 |
| 🐳 | **一键部署** | Docker Compose — 单一命令启动所有服务 |

---

## 系统架构

```
浏览器 ──▶ Next.js 14（端口 3000）
              │
              ▼
        FastAPI（端口 8000）
              │
        ┌─────┴─────┐
        ▼           ▼
   Clawby API    LLM API
   （市场数据）  （OpenAI/Anthropic）
```

- **前端**：Next.js 14、React 18、Tailwind CSS、Recharts、Lucide icons
- **后端**：Python 3.11+、FastAPI、httpx、Jinja2、WeasyPrint
- **数据源**：Clawby API（实时金融数据）
- **LLM**：OpenAI API / Anthropic API / 任何兼容端点
- **部署**：Docker Compose

---

## 工作流程

1. **输入股票代码**（例如 AAPL、MSFT、TSLA）并点击"生成"
2. **后端并行获取所有维度数据**从 Clawby（8+ 并发 API 调用）
3. **使用 Jinja2 提示模板组装数据**成结构化上下文
4. **LLM 通过 SSE 流生成**分析报告
5. **报告通过交互式图表、关键指标和完整 Markdown 呈现**
6. **导出**为 Markdown 或专业 PDF

---

## 配置说明

所有设置通过 `.env` 文件配置：

| 变量 | 必需 | 默认值 | 描述 |
|---|---|---|---|
| `CLAWBY_API_KEY` | ✅ | — | [Clawby](https://www.openclawby.com/) API 密钥（免费） |
| `LLM_API_KEY` | ✅ | — | OpenAI / Anthropic API 密钥 |
| `LLM_PROVIDER_TYPE` | ❌ | `openai` | 提供商类型（`openai` / `anthropic` / `custom_openai`） |
| `LLM_MODEL` | ❌ | `gpt-4o` | 默认模型名称 |
| `BACKEND_PORT` | ❌ | `8000` | 后端端口 |
| `FRONTEND_PORT` | ❌ | `3000` | 前端端口 |

额外的 LLM 提供商可以在运行时通过 **设置 → LLM 提供商** 添加。

---

## 项目结构

```
stock-report/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   ├── config.py            # 配置管理
│   │   ├── routers/             # API 路由（健康检查、数据、报告、提供商、模板）
│   │   ├── services/            # Clawby 客户端、LLM 桥接、演示数据、PDF 导出
│   │   ├── models/              # Pydantic 数据模型
│   │   ├── presets/             # 内置模板
│   │   └── templates/           # Jinja2 提示模板
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/                 # Next.js 页面（主页、报告、设置、历史）
│   │   ├── components/          # React 组件（图表、布局、报告查看器）
│   │   ├── lib/                 # API 客户端 + SSE 流
│   │   └── types/               # TypeScript 类型定义
│   └── Dockerfile
├── docker-compose.yml           # 一键部署配置
├── AGENT_SETUP.md               # AI 代理安装指南（用于 Codex、Claude Code 等）
├── DEVELOPMENT.md               # 完整开发文档（中文）
├── README.zh-CN.md              # 中文文档
└── setup.sh                     # 一键设置脚本
```

---

## AI 代理设置

本项目设计用于由 AI 编码代理（Codex、Claude Code 等）部署。只需给你的代理提供仓库 URL，它就会按照 [`AGENT_SETUP.md`](AGENT_SETUP.md) 中的说明进行操作。

代理将：
1. 克隆仓库
2. 要求你提供 API 密钥
3. 使用 Docker Compose 启动服务
4. 打开浏览器

---

## 开发

完整的开发计划、API 参考和实现细节请参见 [`DEVELOPMENT.md`](DEVELOPMENT.md)（中文）。

---

## 许可证

MIT — 详见 [LICENSE](LICENSE)。

---

*非投资建议。数据来自 Clawby。仅供参考之用。*
