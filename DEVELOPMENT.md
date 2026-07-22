# Clawby US Equity Report Generator — 开发文档

**v0.2-draft** · 2026-07-22

---

## 目录

1. [项目概述](#1-项目概述)
2. [技术栈](#2-技术栈)
3. [项目目录结构](#3-项目目录结构)
4. [API 设计](#4-api-设计)
5. [核心：报告模板系统](#5-核心报告模板系统)
6. [核心：多模型 LLM 配置中心](#6-核心多模型-llm-配置中心)
7. [核心：报告生成流程](#7-核心报告生成流程)
8. [前端 UI 设计 — 金融风格](#8-前端-ui-设计--金融风格)
9. [配置与部署](#9-配置与部署)
10. [AI Agent 安装指引](#10-ai-agent-安装指引)
11. [开发实施优先级](#11-开发实施优先级)
12. [附录：Clawby 接口速查](#12-附录clawby-接口速查)

---

## 1. 项目概述

基于 [Clawby](https://www.openclawby.com/) 数据 API 构建的**美股分析报告生成器**。用户输入一只股票代码，自动聚合行情、做空、暗池、期权、基本面、情绪等多维数据，通过用户指定的大语言模型生成结构化分析报告，支持网页预览、PDF 导出和多模板切换。

### 1.1 设计原则

| 原则 | 说明 |
|---|---|
| **数据驱动** | 报告中每一个结论必须有真实数据支撑，LLM 只做归纳和表达，不编造 |
| **多模型可切换** | 用户可在 UI 中自由增删和选择 LLM 提供商（OpenAI / Anthropic / 本地模型等），无需改代码 |
| **模板开放** | 分析报告的章节、prompt、风格通过模板定义，用户可以复制模板自行定制 |
| **一键部署** | Docker Compose 单机启动，所有配置通过环境变量 + Web UI 完成 |

### 1.2 目标用户

- 美股个人投资者，希望快速获得一份覆盖价格、资金流、衍生品、基本面、情绪等多维度的个股分析报告
- 量化 / 研究团队，将结构化数据 + AI 分析集成到自己的工具链中

---

## 2. 技术栈

### 2.1 Backend — Python (FastAPI)

```
Python 3.11+ · FastAPI · httpx · pydantic-settings · Jinja2 · WeasyPrint
```

| 组件 | 选型理由 |
|---|---|
| **FastAPI** | 异步框架，原生支持 SSE（Server-Sent Events）做报告结果的流式返回 |
| **httpx** | 异步 HTTP 客户端，调用 Clawby API |
| **pydantic-settings** | 从 `.env` + 运行时配置管理所有参数 |
| **Jinja2** | 模板引擎：报告 prompt 模板和 PDF HTML 模板 |
| **WeasyPrint** | HTML → PDF 渲染，支持 CSS 分页、页眉页脚 |
| **无数据库** | 所有数据实时拉取，不做持久化；报告快照可选内存 / 文件缓存 |

### 2.2 Frontend — Next.js 14 (App Router)

```
Node 18+ · React 18 · Next.js 14 · Tailwind CSS · shadcn/ui · Recharts
```

| 组件 | 选型理由 |
|---|---|
| **Next.js 14 App Router** | SSR 首屏快，API routes 可作 BFF 代理 |
| **shadcn/ui** | 开源、可定制的组件库，方便构建金融专业 UI |
| **Recharts** | React 原生图表库（折线图、柱状图、仪表盘） |
| **Tailwind CSS** | 快速实现金融风格的深色主题 |
| **EventSource** | 原生 SSE 订阅，接收 LLM 流式输出 |

### 2.3 Deployment

```yaml
Docker Compose 一键部署
- 前端 (Next.js) + 后端 (FastAPI) 双容器
- 所有配置注入为环境变量
- 可选: Caddy/Nginx 反代 + HTTPS
```

---

## 3. 项目目录结构

```
stock-report/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                        # FastAPI app entry + CORS
│   │   ├── config.py                      # 配置管理（文件 + 环境变量 + 运行时重载）
│   │   │
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   ├── health.py                  # GET /api/health
│   │   │   ├── data.py                    # GET /api/quote, /api/bars ... 原始数据接口
│   │   │   ├── report.py                  # POST /api/report (SSE) + GET /api/report/{id}
│   │   │   ├── templates.py               # CRUD /api/templates — 报告模板管理
│   │   │   └── providers.py               # CRUD /api/providers — LLM 提供商管理
│   │   │
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── clawby.py                  # Clawby HTTP 客户端（所有接口封装）
│   │   │   ├── llm.py                     # LLM 统一客户端（多 Provider 路由）
│   │   │   ├── report.py                  # 报告编排器
│   │   │   └── template.py               # 模板解析 & 渲染引擎
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── schemas.py                 # Pydantic v2 请求/响应模型
│   │   │   ├── provider.py                # LLM Provider 数据模型
│   │   │   └── template.py               # 模板数据模型
│   │   │
│   │   ├── templates/                     # Jinja2 模板文件
│   │   │   ├── prompts/                   # 报告 prompt 模板 (.j2)
│   │   │   │   ├── comprehensive.j2       # 全面分析
│   │   │   │   ├── quick.j2               # 快速概览
│   │   │   │   └── deep_dive.j2          # 深度研究
│   │   │   └── pdf/                       # PDF 样式模板
│   │   │       ├── default.html.j2
│   │   │       └── minimalist.html.j2
│   │   │
│   │   └── presets/                       # 内置预设（模板 & LLM Provider 种子数据）
│   │       ├── templates.json
│   │       └── providers.json
│   │
│   ├── requirements.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── layout.tsx                 # 全局布局（侧边栏 + 顶部导航 + 深色主题）
│   │   │   ├── page.tsx                   # 首页 — 输入 ticker + 生成报告
│   │   │   ├── report/
│   │   │   │   └── [id]/
│   │   │   │       └── page.tsx           # 报告详情页
│   │   │   ├── settings/
│   │   │   │   ├── page.tsx               # 设置主页
│   │   │   │   ├── providers/
│   │   │   │   │   └── page.tsx           # LLM Provider 管理
│   │   │   │   └── templates/
│   │   │   │       └── page.tsx           # 报告模板管理
│   │   │   └── history/
│   │   │       └── page.tsx               # 历史报告
│   │   │
│   │   ├── components/
│   │   │   ├── layout/
│   │   │   │   ├── sidebar.tsx            # 左侧导航栏
│   │   │   │   ├── topbar.tsx             # 顶部状态栏
│   │   │   │   └── theme-provider.tsx
│   │   │   ├── report/
│   │   │   │   ├── report-viewer.tsx      # 报告渲染器（Markdown → 带样式 HTML）
│   │   │   │   ├── report-controls.tsx    # 报告操作（PDF / 刷新 / 分享）
│   │   │   │   ├── progress-bar.tsx       # SSE 进度条
│   │   │   │   └── score-card.tsx         # 评分卡片
│   │   │   ├── charts/
│   │   │   │   ├── chart-price.tsx        # 价格走势 + MA
│   │   │   │   ├── chart-volume.tsx       # 成交量柱状图
│   │   │   │   ├── chart-short.tsx        # 做空趋势多线图
│   │   │   │   ├── chart-darkpool.tsx     # 暗池热力图
│   │   │   │   ├── chart-options.tsx      # 期权链分布
│   │   │   │   └── gauge-sentiment.tsx    # 情绪仪表盘
│   │   │   ├── settings/
│   │   │   │   ├── provider-card.tsx      # LLM Provider 卡片
│   │   │   │   ├── provider-form.tsx      # 编辑 LLM Provider 弹窗
│   │   │   │   ├── template-card.tsx      # 模板卡片
│   │   │   │   └── template-editor.tsx    # 模板编辑器
│   │   │   └── shared/
│   │   │       ├── ticker-input.tsx       # 股票代码输入组件
│   │   │       ├── status-badge.tsx       # 状态标签
│   │   │       └── data-table.tsx         # 数据表格
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts                     # 后端 API 客户端
│   │   │   └── utils.ts                   # 工具函数
│   │   │
│   │   └── types/
│   │       ├── index.ts
│   │       ├── provider.ts
│   │       └── template.ts
│   │
│   ├── public/
│   │   └── logo.svg
│   ├── package.json
│   ├── next.config.ts
│   └── tailwind.config.ts
│
├── docker-compose.yml
├── .env.example
├── setup.sh
├── AGENT_SETUP.md
└── README.md
```

---

## 4. API 设计

### 4.1 后端 REST API 总览

| Method | Path | 描述 |
|---|---|---|
| GET | `/api/health` | 健康检查 + 各 Provider 连通性 |
| | | **数据接口** |
| GET | `/api/quote/{ticker}` | 实时报价 + Screener 快照 |
| GET | `/api/bars/{ticker}` | 近 1 年日线 |
| GET | `/api/short/{ticker}` | 做空数据聚合 |
| GET | `/api/darkpool/{ticker}?date=` | 暗池 levels + summary |
| GET | `/api/options/{ticker}` | 期权链 + Max Pain |
| GET | `/api/financials/{ticker}` | SEC 财务数据（EPS / 收入 / 净利润） |
| GET | `/api/corporate/{ticker}` | 分红 + 拆股 + 流通股本 |
| GET | `/api/sentiment/{ticker}` | Reddit 情绪 |
| | | **报告接口** |
| POST | `/api/report` | 生成报告（SSE 流式） |
| GET | `/api/report/{id}` | 获取指定报告快照 |
| GET | `/api/report-history` | 最近的报告列表 |
| | | **LLM Provider 管理** |
| GET | `/api/providers` | 列出所有已配置的 Provider |
| POST | `/api/providers` | 添加新的 Provider |
| PUT | `/api/providers/{id}` | 更新 Provider 配置 |
| DELETE | `/api/providers/{id}` | 删除 Provider |
| POST | `/api/providers/{id}/test` | 测试 Provider 连通性 |
| PUT | `/api/providers/default` | 设置默认 Provider |
| | | **模板管理** |
| GET | `/api/templates` | 列出所有模板 |
| POST | `/api/templates` | 创建新模板（复制内置模板 + 自定义） |
| PUT | `/api/templates/{id}` | 更新模板 |
| DELETE | `/api/templates/{id}` | 删除模板 |
| GET | `/api/templates/{id}/preview` | 预览模板渲染效果 |

### 4.2 POST /api/report 请求体

```json
{
  "ticker": "AAPL",
  "template_id": "rpt_comprehensive",
  "provider_id": "prov_openai_01",
  "model": "gpt-4o",
  "language": "zh-CN"
}
```

| 字段 | 类型 | 说明 |
|---|---|---|
| ticker | string | 股票代码（1-5 个大写字母） |
| template_id | string | 使用的报告模板 ID |
| provider_id | string | 使用的 LLM Provider ID |
| model | string | 模型名称（如 `gpt-4o`, `claude-sonnet-4-20250514`） |
| language | string | `zh-CN` / `en` |

### 4.3 SSE 事件流

```
event: progress
data: {"step": "validating",          "message": "正在验证股票代码..."}

event: progress
data: {"step": "fetching_quote",     "message": "拉取行情数据..."}

event: progress
data: {"step": "fetching_bars",      "message": "拉取日线走势..."}

event: progress
data: {"step": "fetching_short",     "message": "拉取做空数据..."}

event: progress
data: {"step": "fetching_darkpool",  "message": "拉取暗池数据..."}

event: progress
data: {"step": "fetching_options",   "message": "拉取期权链..."}

event: progress
data: {"step": "fetching_financials","message": "拉取财务基本面..."}

event: progress
data: {"step": "fetching_sentiment", "message": "拉取市场情绪..."}

event: progress
data: {"step": "fetching_corporate", "message": "拉取公司行动..."}

event: progress
data: {"step": "generating",         "message": "AI 正在撰写分析报告（0%）..."}
                                                                  ↑ 百分比逐步递增
event: chunk
data: {"text": "## 1. 公司概览\n\n当前价格: $245.67..."}

event: complete
data: {"id": "rpt_abc123", "markdown": "# AAPL 综合分析报告\n\n..."}

event: error
data: {"code": "provider_unreachable", "message": "无法连接到 LLM Provider，请检查 API Key 或网络"}
```

---

## 5. 核心：报告模板系统

### 5.1 模板数据模型

```python
class ReportTemplate(BaseModel):
    id: str                          # 唯一标识，如 "rpt_comprehensive"
    name: str                        # 用户可读名称，如 "全面分析报告"
    description: str                 # 简短描述
    category: Literal["builtin", "custom"]

    # === 章节配置 ===
    sections: list[SectionDef]       # 报告包含的章节（有序）

    # === Prompt 配置 ===
    system_prompt: str               # LLM System Prompt（Jinja2 模板）
    user_prompt_template: str        # User Prompt 模板（Jinja2 模板）

    # === 数据配置 ===
    required_data: list[str]         # 必须拉取的数据维度 ID 列表
    optional_data: list[str]         # 可选的数据维度 ID

    # === 风格配置 ===
    language: list[str]              # 支持的语言 ["zh-CN", "en"]
    output_format: str               # "markdown" | "html"
    default_model: str | None        # 该模板推荐的模型

    # === PDF 配置 ===
    pdf_css_template: str | None     # 自定义 PDF CSS 模板 ID
    pdf_margin_top: str              # "14mm"
    pdf_margin_bottom: str

    # === 元数据 ===
    created_at: datetime
    updated_at: datetime
    version: int


class SectionDef(BaseModel):
    id: str                          # "overview"
    title: dict[str, str]            # {"zh-CN": "公司概览", "en": "Overview"}
    order: int                       # 章节顺序
    required: bool                   # 是否必含
    data_dependencies: list[str]     # 该章节依赖的数据维度
    chart_hints: list[str]           # 建议在该章节展示的图表
    max_length: int | None           # 该章节建议最大 token 数
```

### 5.2 内置模板预设

系统内置 4 个模板，用户不可编辑但可以复制后修改：

| ID | 名称 | 章节数 | 数据维度数 | 适用场景 |
|---|---|---|---|---|
| `rpt_comprehensive` | 全面分析报告 | 8 | 全量（10+） | 深度调研 |
| `rpt_quick` | 快速概览 | 4 | 5（quote / bars / short / financials） | 盘中快速判断 |
| `rpt_deep_dive` | 深度研究 | 10 | 全量 + 额外 SEC 字段 | 投资备忘录 |
| `rpt_earnings` | 财报解读 | 5 | financials / quote / sentiment | 财报后快速复盘 |

### 5.3 Prompt 模板示例

以 `rpt_comprehensive` 的 System Prompt 为例（Jinja2）：

```jinja2
你是一位专业的美股分析师。你的任务是基于用户提供的真实多维数据，撰写一份结构化的个股分析报告。

## 报告语言
请使用 {{ language_name }} 撰写全文（包括章节标题）。

## 报告结构
你必须严格按照以下章节顺序输出：
{% for section in sections %}
### {{ section.order }}. {{ section.title[language] }}
{% endfor %}

## 写作要求
1. **所有数据必须来源于提供的 context**，不得编造任何数字。
2. 每个数据点必须给出具体数值（价格、百分比、金额等）。
3. 对于有时间序列的数据，描述趋势方向（上升 / 下降 / 震荡）和幅度。
4. 评分（第8章）每个维度给出 1-10 分并附理由，总分取加权平均。
5. 使用专业的金融分析语气，避免夸张或营销式表述。
6. 如果某维度的数据为空或不可用，明确说明"该维度暂无可用数据"。

## 输出格式
使用 Markdown，其中 ## 为一级标题、### 为二级标题。
图表位置用占位符标注：![chart:chart_id]

## 其他
- 文末标注："报告生成时间: {{ generation_time }}"
- 文末标注："数据来源: Clawby"
- 文末标注："Not investment advice."
```

User Prompt 模板示例：

```jinja2
请基于以下 {{ ticker }} 的多维数据撰写一份 {{ template_name }}。

## 当前价格 & 行情快照
```json
{{ quote_data | tojson(indent=2) }}
```

## 日线走势（近 365 天）
```json
{{ bars_data | tojson(indent=2) }}
```

## 做空数据
```json
{{ short_data | tojson(indent=2) }}
```

## 暗池数据
```json
{{ darkpool_data | tojson(indent=2) }}
```

## 期权链
```json
{{ options_data | tojson(indent=2) }}
```

## 财务基本面
```json
{{ financials_data | tojson(indent=2) }}
```

## 公司行动
```json
{{ corporate_data | tojson(indent=2) }}
```

## Reddit 情绪
```json
{{ sentiment_data | tojson(indent=2) }}
```
```

### 5.4 模板 API 交互

**用户在设置页面的操作流程：**

1. 进入 "报告模板" 页面，看到内置模板列表（只读标记）和自定义模板列表
2. 点击内置模板的「复制」按钮 → 生成一份可编辑的自定义副本
3. 在模板编辑器中：
   - 勾选/取消勾选章节
   - 拖动排序章节
   - 修改 System Prompt 和 User Prompt 模板
   - 选择该模板偏好的 LLM Provider + 模型
   - 调整 PDF 边距和 CSS
4. 点击「测试预览」→ 后端用该模板生成一份报告预览（使用缓存数据）
5. 保存

---

## 6. 核心：多模型 LLM 配置中心

### 6.1 Provider 数据模型

```python
class LLMProvider(BaseModel):
    id: str                          # 唯一标识，如 "prov_openai_01"
    name: str                        # 用户命名，如 "我的 OpenAI"
    provider_type: str               # "openai" | "anthropic" | "custom_openai"

    # === 连接配置 ===
    api_base: str                    # API 地址
    api_key: str                     # (加密存储)
    default_model: str               # 默认模型名

    # === 能力声明 ===
    supported_models: list[str]      # 可选的模型列表
    max_tokens: int                  # 最大输出 token
    supports_streaming: bool         # 是否支持流式

    # === 状态 ===
    is_default: bool                 # 是否为当前默认 Provider
    is_available: bool               # 上次连通性测试结果
    last_tested_at: datetime | None

    # === 元数据 ===
    created_at: datetime
    updated_at: datetime
    error_message: str | None        # 上次测试失败的详细信息
```

### 6.2 支持的 Provider 类型

| type | API Base 默认值 | 默认模型 | 备注 |
|---|---|---|---|
| `openai` | `https://api.openai.com/v1` | `gpt-4o` | 标准 OpenAI |
| `anthropic` | `https://api.anthropic.com` | `claude-sonnet-4-20250514` | 标准 Anthropic |
| `custom_openai` | 用户自定义 | 用户自定义 | 兼容 OpenAI API 格式的任何服务（Azure / Groq / DeepSeek / Ollama 等） |
| `custom_anthropic` | 用户自定义 | 用户自定义 | 兼容 Anthropic API 格式 |

### 6.3 Provider 配置管理

**存储方式：** 后端以 JSON 文件存储于 `backend/app/providers.json`（无数据库依赖）。运行时加载到内存。

```json
[
  {
    "id": "prov_openai_01",
    "name": "我的 OpenAI",
    "provider_type": "openai",
    "api_base": "https://api.openai.com/v1",
    "api_key": "sk-encrypted-xxx",
    "default_model": "gpt-4o",
    "supported_models": ["gpt-4o", "gpt-4o-mini", "o3-mini"],
    "max_tokens": 16384,
    "supports_streaming": true,
    "is_default": true,
    "is_available": true,
    "last_tested_at": "2026-07-22T15:30:00Z",
    "created_at": "2026-07-22T12:00:00Z",
    "updated_at": "2026-07-22T15:30:00Z"
  },
  {
    "id": "prov_anthropic_01",
    "name": "Anthropic Claude",
    "provider_type": "anthropic",
    "api_base": "https://api.anthropic.com",
    "api_key": "sk-ant-encrypted-xxx",
    "default_model": "claude-sonnet-4-20250514",
    "supported_models": ["claude-sonnet-4-20250514", "claude-3-5-sonnet-20241022"],
    "max_tokens": 8192,
    "supports_streaming": true,
    "is_default": false,
    "is_available": false,
    "last_tested_at": "2026-07-22T15:25:00Z",
    "created_at": "2026-07-22T14:00:00Z",
    "updated_at": "2026-07-22T15:25:00Z"
  },
  {
    "id": "prov_deepseek_01",
    "name": "DeepSeek (自部署)",
    "provider_type": "custom_openai",
    "api_base": "https://api.deepseek.com/v1",
    "api_key": "sk-encrypted-xxx",
    "default_model": "deepseek-chat",
    "supported_models": ["deepseek-chat", "deepseek-reasoner"],
    "max_tokens": 8192,
    "supports_streaming": true,
    "is_default": false,
    "is_available": true,
    "last_tested_at": "2026-07-22T15:20:00Z",
    "created_at": "2026-07-22T13:00:00Z",
    "updated_at": "2026-07-22T15:20:00Z"
  }
]
```

### 6.4 连通性测试

`POST /api/providers/{id}/test` 执行步骤：

1. 使用 Provider 配置向 `/v1/chat/completions`（OpenAI 格式）或 `/v1/messages`（Anthropic 格式）发送一条最简单的消息
2. 等待响应（超时 15 秒）
3. 如果成功 → 更新 `is_available=true, last_tested_at=now, error_message=null`
4. 如果失败 → 更新 `is_available=false, error_message="具体错误信息"`
5. 返回测试结果

### 6.5 Provider API 交互

**用户在设置页面的操作流程：**

1. 进入 "LLM Providers" 页面，看到所有已配置的 Provider 卡片列表
2. 每个卡片显示：名称、类型、默认模型、状态指示灯（绿色=可用 / 红色=不可用）
3. 点击「添加 Provider」→ 弹出表单：
   - 选择 Provider 类型（OpenAI / Anthropic / 自定义兼容）
   - 输入名称（如 "公司内网 LLM"）
   - 输入 API Base URL
   - 输入 API Key（密码字段，输入时明文，保存后加密）
   - 输入默认模型名
   - 可选：支持的模型列表（逗号分隔）
4. 点击「测试连接」→ 后端执行连通性测试，前端显示结果
5. 点击「设为默认」→ 该 Provider 在报告生成时自动选中
6. 生成报告时，如果 ticker 已输入过，下拉框列出所有可用的 Provider，并根据 Default 标记自动选择

---

## 7. 核心：报告生成流程

`services/report.py` 中 `generate_report()` 的完整状态机：

```
                      ┌─────────────┐
                      │  VALIDATING  │ ← 校验 ticker 格式 + 检查 Provider 连通性
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │  FETCHING   │ ← 并行拉取模板所需的全部数据维度
                      │  (ALL AT    │   (asyncio.gather, 所有 HTTP 请求同时发起)
                      │   ONCE)     │
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │  ASSEMBLING │ ← 数据聚合 + 渲染 Jinja2 模板
                      │             │   → context dict + 完整 prompt
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │ GENERATING  │ ← 调用 LLM stream，逐 chunk 通过 SSE 推送
                      │ (STREAMING) │
                      └──────┬──────┘
                             │
                      ┌──────▼──────┐
                      │  COMPLETE   │ ← 保存报告快照 + 发送 complete 事件
                      └─────────────┘
```

### 7.1 数据拉取并发度

```python
async def fetch_all_data(ticker: str, template: ReportTemplate) -> DataBundle:
    tasks = {}

    # 根据模板的 required_data + optional_data 决定拉取哪些维度
    for dim_id in template.required_data:
        tasks[dim_id] = asyncio.create_task(data_fetchers[dim_id](ticker))

    for dim_id in template.optional_data:
        # 可选维度超时 10 秒，超时不阻塞整体
        tasks[dim_id] = asyncio.create_task(
            asyncio.wait_for(data_fetchers[dim_id](ticker), timeout=10)
        )

    results = {}
    for dim_id, task in tasks.items():
        try:
            results[dim_id] = await task
        except (asyncio.TimeoutError, ClawbyAPIError) as e:
            results[dim_id] = {"error": str(e), "data": None}

    return DataBundle(**results)
```

### 7.2 LLM 调用桥接

```python
class LLMService:
    def __init__(self):
        self._providers: dict[str, LLMProvider] = {}  # 从 providers.json 加载

    async def generate_stream(
        self,
        provider_id: str,
        model: str,
        system_prompt: str,
        user_prompt: str,
    ) -> AsyncIterator[str]:
        provider = self._providers[provider_id]

        if provider.provider_type == "openai" or provider.provider_type == "custom_openai":
            async with httpx.AsyncClient() as client:
                async with client.stream(
                    "POST",
                    f"{provider.api_base}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {provider.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "stream": True,
                    },
                ) as response:
                    async for line in response.aiter_lines():
                        if line.startswith("data: "):
                            chunk = line[6:]
                            if chunk != "[DONE]":
                                # 解析 delta
                                ...

        elif provider.provider_type == "anthropic" or provider.provider_type == "custom_anthropic":
            # Anthropic SSE 格式
            ...
```

---

## 8. 前端 UI 设计 — 金融风格

### 8.1 设计语言

| 维度 | 规范 |
|---|---|
| **主题** | 深色为主（`#0a0e17` 背景），搭配浅色强调色（`#00c853` 绿色涨 / `#ff1744` 红色跌） |
| **字体** | 英文: Inter + JetBrains Mono (数据表格)；中文: Noto Sans SC |
| **配色** | 主色 `#1a73e8` · 次级 `#2d3748` · 正涨 `#26a69a` · 负跌 `#ef5350` · 警告 `#ffa726` |
| **布局** | 固定左侧导航（240px）+ 顶部状态栏（56px）+ 内容区域 |
| **数据密度** | 高密度，表格可横向滚动，支持快捷键 |

### 8.2 页面 & 路由

```
/                   → 首页（输入 ticker + 生成报告）
/report/[id]        → 报告详情
/settings           → 设置首页
/settings/providers → LLM Provider 管理
/settings/templates → 报告模板管理
/history            → 历史报告
```

### 8.3 首页低保真

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [Logo] Clawby Report                [⚙ 设置] [📄 历史]   状态: OpenAI ✅  │
├────────────────────────────────────────────────────────────────────────────┤
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │                                                                        ││
│  │   ┌──────────────────────────────────────┐   [生成报告]                 ││
│  │   │ 输入股票代码  e.g. AAPL, MSFT, TSLA  │   ⏎                         ││
│  │   └──────────────────────────────────────┘                             ││
│  │                                                                        ││
│  │   ┌────────────┐  ┌────────────┐  ┌───────────────────┐               ││
│  │   │ 全面分析    │  │ 快速概览    │  │ LLM: GPT-4o ▼     │               ││
│  │   └────────────┘  └────────────┘  └───────────────────┘               ││
│  │                                                                        ││
│  │   最近: AAPL · MSFT · NVDA · TSLA · AMZN                               ││
│  │                                                                        ││
│  └────────────────────────────────────────────────────────────────────────┘│
│  ┌────────────────────────────────────────────────────────────────────────┐│
│  │  今日市场概览                                                          ││
│  │  S&P 500: ▲ 5,584.12  +0.32%    Nasdaq: ▲ 18,343.22  +0.56%          ││
│  │  DJIA: ▼ 41,250.11  -0.18%      VIX: 12.54  ▼ -2.3%                  ││
│  └────────────────────────────────────────────────────────────────────────┘│
└────────────────────────────────────────────────────────────────────────────┘
```

### 8.4 报告页低保真

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [Logo]  ← 返回                  AAPL 全面分析报告     [📥 PDF] [🔄 刷新]  │
├────────────────────────────────────────────────────────────────────────────┤
│ 生成于 2026-07-22 16:30 · GPT-4o · 全面分析模板                            │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌─── 关键指标卡片 ─────────────────────────────────────────────────────┐ │
│  │  $245.67    +1.23%    $3.18T      65.2M      $6.78     36.2x       │ │
│  │  当前价格   日涨跌     市值        成交量     TTM EPS    P/E         │ │
│  │  52W高: 260.10  52W低: 170.33  做空比: 2.1%   Beta: 1.21            │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─── 价格走势 ─────────────────────────────────────────────────────────┐ │
│  │    ┌──────────────────────────────────────────────────────┐          │ │
│  │    │            Recharts: 折线图 + 成交量柱 + MA20/MA50   │          │ │
│  │    └──────────────────────────────────────────────────────┘          │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─── 做空与资金流 ──────────────────────────────────────────────────────┐ │
│  │  ┌──────────────────────┐  ┌──────────────────────┐                   │ │
│  │  │  短成交量 / 借券费率  │  │  暗池分布热力图       │                   │ │
│  │  └──────────────────────┘  └──────────────────────┘                   │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ┌─── 期权链 ────────────────────────────────────────────────────────────┐ │
│  │  最大痛点: $240 · 最近到期: 2026-08-21                                │ │
│  │  ┌──────────────────────────────────────────────────────┐             │ │
│  │  │            Call/Put OI 分布柱状图                     │             │ │
│  │  └──────────────────────────────────────────────────────┘             │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ════════════════════════════════════════════════════════════════════════ │
│  ## 1. 公司概览 & 行情摘要                                                │
│                                                                           │
│  Apple Inc. 当前股价 $245.67，日内上涨 1.23%，总市值 3.18 万亿美元...     │
│  ...                                                                      │
│                                                                           │
│  ## 2. 价格走势与技术分析                                                  │
│  ![chart:price]                                                           │
│  近一年 AAPL 呈现上升通道，52W 涨幅 44.5%...                               │
│  ...                                                                      │
│                                                                           │
│  ## 3. 资金流向                                                            │
│  ![chart:short] ![chart:darkpool]                                         │
│  当前做空占比 2.1%，处于历史低位...                                        │
│  ...                                                                      │
│                                                                           │
│  ## 8. 综合评分                                                            │
│  ┌────┬────┬────┬────┬────┬─────────────────────────────────────────┐   │
│  │价格│资金│期权│基本│情绪│  总分: 7.2/10 · 偏多                    │   │
│  │ 7  │ 6  │ 8  │ 7  │ 8  │  短期看多，中期注意估值回归风险          │   │
│  └────┴────┴────┴────┴────┴─────────────────────────────────────────┘   │
│                                                                           │
│  ---                                                                      │
│  报告生成时间: 2026-07-22 16:30 UTC+8                                     │
│  数据来源: Clawby · 模型: GPT-4o                                          │
│  Not investment advice.                                                    │
└────────────────────────────────────────────────────────────────────────────┘
```

### 8.5 设置页 — LLM Provider 管理

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [Logo]  设置 / LLM Providers                                               │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────────────────────────────────────────────┐  [+ 添加]  │
│  │  [● 可用] GPT-4o                                        │  [编辑] [│] │
│  │  OpenAI · api.openai.com/v1                              │  测试     │
│  │  默认模型: gpt-4o · 流量: 流式 ✓                        │  [+默认]  │
│  │  上次测试: 2026-07-22 15:30 · 连通 ✓                     │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────┐  [编辑] [│] │
│  │  [○ 不可用] Claude Sonnet 4                             │  测试     │
│  │  Anthropic · api.anthropic.com                           │           │
│  │  默认模型: claude-sonnet-4-20250514 · 流量: 流式 ✓      │           │
│  │  上次测试: 2026-07-22 15:25 · 错误: 401 Unauthorized    │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                           │
│  ┌──────────────────────────────────────────────────────────┐  [编辑] [│] │
│  │  [● 可用] DeepSeek V3                                   │  测试     │
│  │  自定义 API · api.deepseek.com/v1                        │           │
│  │  默认模型: deepseek-chat · 流量: 流式 ✓                  │           │
│  │  支持: deepseek-chat, deepseek-reasoner                   │           │
│  └──────────────────────────────────────────────────────────┘           │
│                                                                           │
└────────────────────────────────────────────────────────────────────────────┘
```

### 8.6 设置页 — 模板编辑

```
┌────────────────────────────────────────────────────────────────────────────┐
│ [Logo]  设置 / 报告模板 / 编辑「全面分析报告」                             │
├────────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  模板名称: [全面分析报告]                                                  │
│  描述:     [覆盖行情、做空、暗池、期权、基本面、情绪的完整分析]             │
│                                                                           │
│  ─── 章节配置 ─────────────────────────────────────────────────────────── │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │  ☑ 1. 公司概览 & 行情摘要                    [数据: quote] [📊 价格] │ │
│  │  ☑ 2. 价格走势与技术分析                      [数据: bars]  [📊 MA]  │ │
│  │  ☑ 3. 资金流向（做空/暗池）                 [数据: short,dp] [📊]   │ │
│  │  ☑ 4. 期权市场分析                          [数据: options] [📊]    │ │
│  │  ☑ 5. 基本面分析                            [数据: financials]      │ │
│  │  ☑ 6. 市场情绪                              [数据: sentiment] [📊]  │ │
│  │  ☑ 7. 投资亮点 & 风险提示                   []                       │ │
│  │  ☑ 8. 综合评分                              []                       │ │
│  │  [☰ 拖动手柄可调整顺序]                                              │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ─── Prompt 模板 ──────────────────────────────────────────────────────── │
│  [系统 Prompt]                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 你是一位专业的美股分析师... (Jinja2 编辑器)                          │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  [用户 Prompt]                                                            │
│  ┌──────────────────────────────────────────────────────────────────────┐ │
│  │ 请基于以下 {{ ticker }} 的多维数据...                                │ │
│  └──────────────────────────────────────────────────────────────────────┘ │
│                                                                           │
│  ─── LLM 偏好 ────────────────────────────────────────────────────────── │
│  默认 Provider: [GPT-4o ▼]  默认模型: [gpt-4o ▼]                         │
│                                                                           │
│  ─── PDF 样式 ─────────────────────────────────────────────────────────── │
│  CSS 模板: [default ▼]  上边距: [14mm]  下边距: [16mm]                   │
│                                                                           │
│  [💾 保存]  [🔍 预览报告]  [↩ 取消]                                      │
└────────────────────────────────────────────────────────────────────────────┘
```

### 8.7 金融风格组件说明

| 组件 | 视觉特征 |
|---|---|
| **关键指标卡片** | 深色背景 `#1a1d2e`，关键数字白色大号字体，标签灰色，涨跌用红绿色标注 |
| **数据表格** | 隔行交替色，可排序，可横向滚动，数字右对齐 |
| **图表** | 深色背景，白色网格线，涨跌颜色，可缩放/悬停提示 |
| **进度指示** | 线性进度条 + 当前步骤文字 |
| **Provider 卡片** | 左侧状态指示灯（绿/红/灰圆点），名称+型号+状态描述 |
| **评分仪表盘** | 圆环或径向条，五维雷达图 + 总分 |
| **加载骨架屏** | 报告加载时显示与最终内容结构一致的灰色条纹骨架 |

---

## 9. 配置与部署

### 9.1 环境变量 (.env)

```bash
# === 必需 ===
CLAWBY_API_KEY=pk_xxx

# === LLM Provider（仅用于初始默认，后续可在 UI 中修改） ===
# 如果.env 中有配置，首次启动时自动导入为默认 Provider
LLM_PROVIDER_TYPE=openai
LLM_API_BASE=https://api.openai.com/v1
LLM_API_KEY=sk-xxx
LLM_MODEL=gpt-4o

# === 可选 ===
BACKEND_PORT=8000
FRONTEND_PORT=3000
LANGUAGE=zh-CN
```

### 9.2 Docker Compose

```yaml
services:
  backend:
    build: ./backend
    ports: ["${BACKEND_PORT:-8000}:8000"]
    env_file: .env
    volumes:
      - ./backend/app/providers.json:/app/providers.json  # 持久化 Provider 配置
      - ./backend/app/templates.json:/app/templates.json   # 持久化模板配置
      - ./backend/app/reports:/app/reports                 # 持久化报告快照

  frontend:
    build: ./frontend
    ports: ["${FRONTEND_PORT:-3000}:3000"]
    environment:
      NEXT_PUBLIC_API_URL: http://localhost:8000
    depends_on: [backend]
```

### 9.3 setup.sh

```bash
#!/usr/bin/env bash
set -e

echo "==========================================="
echo "  Clawby Stock Report Generator — Setup"
echo "==========================================="

# 1. 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi

# 2. 配置
if [ ! -f .env ]; then
    cp .env.example .env
    echo ""
    echo "⚠️  请编辑 .env 文件，填入以下配置："
    echo "    - CLAWBY_API_KEY (https://www.openclawby.com/ 注册获取)"
    echo "    - LLM_API_KEY (OpenAI / Anthropic API Key)"
    echo ""
    echo "完成后重新运行 setup.sh"
    exit 0
fi

# 3. 启动
echo "🚀 启动服务..."
docker compose up -d --build

echo ""
echo "✅ 启动完成！"
echo "   前端: http://localhost:${FRONTEND_PORT:-3000}"
echo "   后端: http://localhost:${BACKEND_PORT:-8000}"
```

---

## 10. AI Agent 安装指引

`AGENT_SETUP.md` 完整内容，设计为代码助手（Codex / Claude Code 等）可直接理解执行的步骤。

```markdown
# Agent Setup Guide

## 给你的 AI 助手

请按以下步骤安装和启动 Stock Report Generator。

### 步骤 1: 克隆仓库

\`\`\`bash
git clone <仓库地址>
cd stock-report
\`\`\`

### 步骤 2: 配置环境变量

\`\`\`bash
cp .env.example .env
\`\`\`

**需要用户提供以下信息**（让用户填写或直接给出）：

1. **Clawby API Key** — 免费注册于 [https://www.openclawby.com/](https://www.openclawby.com/)
2. **LLM API Key**（任选一个）:
   - OpenAI: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Anthropic: [https://console.anthropic.com/](https://console.anthropic.com/)

填入 `.env` 文件后，执行下一步。

### 步骤 3: 启动服务

\`\`\`bash
# 推荐方式（Docker，无需手动装依赖）
docker compose up -d --build

# 或本地开发方式
# cd backend  && pip install -r requirements.txt && uvicorn app.main:app --reload --port 8000
# cd frontend && npm install && npm run dev
\`\`\`

### 步骤 4: 访问

打开浏览器访问 [http://localhost:3000](http://localhost:3000)

### 步骤 5: 配置 LLM Provider（可选）

启动后，进入设置 > LLM Providers：
1. 如果 .env 中已有配置，系统会自动导入默认 Provider
2. 可以添加更多 Provider（Anthropic、DeepSeek、Ollama 等）
3. 点击 "测试连接" 验证连通性
4. 将其中一个设为默认

现在就可以生成第一份美股分析报告了。
```

---

## 11. 开发实施优先级

| Phase | 内容 | 估算 |
|---|---|---|
| **Phase 1: 后端骨架** | FastAPI app + 配置管理 + Clawby 客户端 + 所有原始数据 API 路由 + 健康检查 | 2-3 天 |
| **Phase 2: LLM 集成** | Provider 模型 + 统一 LLM 客户端（OpenAI / Anthropic / Custom）+ SSE 流式 + 连通性测试 | 1-2 天 |
| **Phase 3: 报告编排** | 模板数据模型 + Jinja2 Prompt 渲染 + 报告生成状态机 + 并发的数据拉取 + 报告快照 | 2 天 |
| **Phase 4: 前端骨架** | Next.js 项目 + 深色主题 + 布局（侧边栏 + 顶部栏）+ 首页输入 + 设置页路由 | 2 天 |
| **Phase 5: Provider 管理 UI** | Provider CRUD 页面 + Provider 卡片 + 添加/编辑表单 + 测试连接按钮 | 1 天 |
| **Phase 6: 模板管理 UI** | 模板列表 + 模板编辑器（章节排序 + Prompt 编辑 + PDF 样式） | 1-2 天 |
| **Phase 7: 报告生成 & 展示** | SSE 进度订阅 + 报告 Markdown 渲染 + 关键指标卡片 + 评分组件 | 1-2 天 |
| **Phase 8: 图表组件** | 5 个 Recharts 可视化组件（价格/成交量/做空/暗池/情绪）+ 数据格式化 | 2 天 |
| **Phase 9: PDF 导出** | HTML → PDF（WeasyPrint）+ PDF CSS 模板 + 下载按钮 | 1 天 |
| **Phase 10: 部署 & 开源** | Docker Compose + setup.sh + AGENT_SETUP.md + README + LICENSE + 开源发布 | 1 天 |

---

## 12. 附录：Clawby 接口速查

所有接口调用方式：

```bash
curl -s -X POST https://api.openclawby.com/api/relay \
  -H "X-API-Key: $CLAWBY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "<interface_name>", "params": {...}}'
```

### 美股相关接口一览

| 用途 | Interface Name | 关键参数 |
|---|---|---|
| 实时行情 | Screen thousands of stocks | `{symbol: "AAPL", view_cols: "display,reg_price,market_cap,..."}` ⚠️ 裸代码 |
| 日线 OHLC | Stock aggregate OHLC bars | `{symbol: "US:AAPL", agg_type: "day", start: <unix>}` |
| 短成交量 | Short volume for a given stock | `{symbol: "US:AAPL"}` |
| 短利息 | Short Interest for a given stock | `{symbol: "US:AAPL"}` |
| 每日短利息 | Daily Short Interest for a given stock | `{symbol: "US:AAPL"}` |
| 借券费率 | Cost-to-borrow from Interactive Brokers | `{symbol: "US:AAPL"}` |
| FTDs | FTDs for a given stock | `{symbol: "US:AAPL"}` |
| 暗池分布 | Dark Pool Levels for a given stock | `{symbol: "US:AAPL", date: "YYYY-MM-DD", decimals: "2"}` |
| 暗池成交 | Dark Pool Prints (trades) summary | `{symbol: "US:AAPL", date: "YYYY-MM-DD"}` |
| 期权链 | Option chain summary | `{underlying: "US:AAPL", expiration: "YYYY-MM-DD"}` |
| 分红 | Dividends for a given stock | `{symbol: "US:AAPL"}` |
| 拆股 | Splits for a given stock | `{symbol: "US:AAPL"}` |
| 流通股本 | Historical Float and Shares Outstanding | `{symbol: "US:AAPL"}` |
| Reddit | Reddit mentions for a given stock | `{symbol: "US:AAPL"}` |
| SEC 查找 | sec_cik_lookup | `{company: "Apple Inc"}` ⚠️ 全称非代码 |
| SEC 财务 | sec_company_concept | `{cik: "320193", concept: "NetIncomeLoss"}` |
| 交易所量 | Exchange volume for a given stock | `{symbol: "US:AAPL"}` |
