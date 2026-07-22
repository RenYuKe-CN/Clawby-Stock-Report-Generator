#!/usr/bin/env bash
set -euo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Clawby Stock Report Generator — Setup${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""

# ── 1. Check prerequisites ──────────────────────────────────────────────────

echo -e "${YELLOW}[1/3]${NC} 检查系统依赖..."

if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker not found.${NC}"
    echo "   请先安装 Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ docker compose not found.${NC}"
    echo "   请安装 Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "   ${GREEN}✓${NC} Docker $(docker --version)"
echo -e "   ${GREEN}✓${NC} $(docker compose version)"
echo ""

# ── 2. Configuration ────────────────────────────────────────────────────────

echo -e "${YELLOW}[2/3]${NC} 配置环境变量..."

if [ ! -f .env ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠️  .env 文件已创建，请编辑并填入以下信息：${NC}"
    echo ""
    echo "   1. CLAWBY_API_KEY — 在 https://www.openclawby.com/ 注册获取"
    echo "   2. LLM_API_KEY — OpenAI / Anthropic 的 API Key"
    echo ""
    echo "   编辑完成后重新运行 setup.sh"
    exit 0
else
    echo -e "   ${GREEN}✓${NC} .env 文件已存在"
fi
echo ""

# ── 3. Launch ───────────────────────────────────────────────────────────────

echo -e "${YELLOW}[3/3]${NC} 构建并启动服务..."
echo ""

docker compose up -d --build

echo ""
echo -e "${GREEN}✅ 启动完成！${NC}"
echo ""
echo "   前端地址: http://localhost:${FRONTEND_PORT:-3000}"
echo "   后端地址: http://localhost:${BACKEND_PORT:-8000}"
echo "   后端健康检查: http://localhost:${BACKEND_PORT:-8000}/api/health"
echo ""
echo -e "${YELLOW}提示:${NC} 首次启动后，可以在设置页面管理 LLM Provider 和报告模板"
echo ""
