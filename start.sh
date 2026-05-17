#!/bin/bash
set -e

# ============================================================
# AI-Collab-OS Quick Start Script
# ============================================================

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}🚀 AI-Collab-OS 启动脚本${NC}"
echo "================================================"

# Check prerequisites
command -v docker >/dev/null 2>&1 || { echo -e "${RED}❌ 需要安装 Docker${NC}"; exit 1; }
command -v docker compose >/dev/null 2>&1 || { echo -e "${RED}❌ 需要安装 Docker Compose V2${NC}"; exit 1; }

# Check .env file
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  未找到 .env 文件，从 .env.example 复制...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}   请编辑 .env 文件配置密钥后重新运行${NC}"
    exit 1
fi

# Parse command
case "${1:-up}" in
    up|start)
        echo -e "${GREEN}▶ 启动所有服务...${NC}"
        docker compose up -d --build
        echo ""
        echo -e "${GREEN}✅ 服务已启动${NC}"
        echo "   前端:  http://localhost:3000"
        echo "   后端:  http://localhost:8000"
        echo "   API文档: http://localhost:8000/docs (仅开发环境)"
        echo ""
        echo "查看日志: docker compose logs -f"
        ;;
    down|stop)
        echo -e "${YELLOW}⏹ 停止所有服务...${NC}"
        docker compose down
        echo -e "${GREEN}✅ 已停止${NC}"
        ;;
    restart)
        echo -e "${YELLOW}🔄 重启所有服务...${NC}"
        docker compose down
        docker compose up -d --build
        echo -e "${GREEN}✅ 已重启${NC}"
        ;;
    logs)
        docker compose logs -f "${2:-}"
        ;;
    status)
        docker compose ps
        echo ""
        echo -e "${GREEN}健康检查:${NC}"
        curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "后端未响应"
        ;;
    migrate)
        echo -e "${GREEN}▶ 运行数据库迁移...${NC}"
        docker compose exec backend alembic upgrade head
        echo -e "${GREEN}✅ 迁移完成${NC}"
        ;;
    clean)
        echo -e "${RED}⚠️  清理所有容器和数据卷...${NC}"
        read -p "确定要删除所有数据？(y/N) " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            docker compose down -v --rmi local
            echo -e "${GREEN}✅ 已清理${NC}"
        fi
        ;;
    *)
        echo "用法: ./start.sh [命令]"
        echo ""
        echo "命令:"
        echo "  up|start    启动所有服务 (默认)"
        echo "  down|stop   停止所有服务"
        echo "  restart     重启所有服务"
        echo "  logs [svc]  查看日志"
        echo "  status      查看状态和健康检查"
        echo "  migrate     运行数据库迁移"
        echo "  clean       清理容器和数据卷"
        ;;
esac
