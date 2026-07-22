# AI Agent 安装指引

本文档专为代码助手（Codex / Claude Code / OpenClaw 等）设计。将仓库地址交给您的 AI 助手，它会自动按以下步骤完成安装。

---

## 给你的 AI 助手

请按以下步骤安装并启动 Stock Report Generator。

### 步骤 1: 克隆仓库

```bash
git clone <仓库地址>
cd stock-report
```

### 步骤 2: 配置环境变量

```bash
cp .env.example .env
```

**需要用户提供：**

1. **Clawby API Key** — 免费注册于 [https://www.openclawby.com/](https://www.openclawby.com/)
2. **LLM API Key**（任选一个）:
   - OpenAI: [https://platform.openai.com/api-keys](https://platform.openai.com/api-keys)
   - Anthropic: [https://console.anthropic.com/](https://console.anthropic.com/)

请让用户将以上信息填入 `.env` 文件后继续。

### 步骤 3: 启动服务

```bash
# Docker 方式（推荐）
docker compose up -d --build
```

或本地开发：

```bash
# 终端 1: 启动后端
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 终端 2: 启动前端
cd frontend
npm install
npm run dev
```

### 步骤 4: 访问

打开浏览器访问 [http://localhost:3000](http://localhost:3000)

### 步骤 5: 配置 LLM Provider（可选）

启动后，在设置 > LLM Providers 中：
1. 如果 `.env` 中已有配置，系统会自动导入为默认 Provider
2. 可以添加更多 Provider（Anthropic、DeepSeek、本地 Ollama 等）
3. 点击 "测试连接" 验证连通性
4. 设为默认后即可生成报告

### 常见 AI Agent 命令速查

```bash
# 查看日志
docker compose logs -f backend
docker compose logs -f frontend

# 重启
docker compose restart

# 停止
docker compose down

# 更新（拉取最新代码后）
docker compose up -d --build
```
