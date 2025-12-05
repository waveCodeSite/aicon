#!/bin/bash

# AICG平台 Docker 部署脚本
# 用法: ./scripts/deploy.sh [命令]
# 命令: start | stop | restart | logs | status | build | migrate | clean

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目根目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
COMPOSE_FILE="$PROJECT_ROOT/docker-compose.prod.yml"
ENV_FILE="$PROJECT_ROOT/.env.prod"

# 检查 .env.prod 是否存在
check_env() {
    if [ ! -f "$ENV_FILE" ]; then
        echo -e "${YELLOW}警告: .env.prod 文件不存在${NC}"
        echo -e "请复制 .env.prod.example 为 .env.prod 并修改配置"
        echo -e "  cp .env.prod.example .env.prod"
        exit 1
    fi
}

# 显示帮助信息
show_help() {
    echo "AICG平台 Docker 部署脚本"
    echo ""
    echo "用法: $0 [命令]"
    echo ""
    echo "命令:"
    echo "  start     启动所有服务"
    echo "  stop      停止所有服务"
    echo "  restart   重启所有服务"
    echo "  logs      查看日志 (可选参数: 服务名)"
    echo "  status    查看服务状态"
    echo "  build     构建镜像"
    echo "  migrate   运行数据库迁移"
    echo "  clean     清理停止的容器和未使用的镜像"
    echo "  shell     进入后端容器 shell"
    echo ""
    echo "示例:"
    echo "  $0 start          # 启动所有服务"
    echo "  $0 logs backend   # 查看后端日志"
    echo "  $0 build          # 重新构建镜像"
}

# 启动服务
start_services() {
    check_env
    echo -e "${GREEN}启动 AICG 平台服务...${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d
    echo -e "${GREEN}服务启动完成!${NC}"
    echo ""
    echo "访问地址:"
    echo "  前端应用: http://localhost"
    echo "  后端API: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo "  MinIO控制台: http://localhost:9001"
}

# 停止服务
stop_services() {
    echo -e "${YELLOW}停止 AICG 平台服务...${NC}"
    docker-compose -f "$COMPOSE_FILE" down
    echo -e "${GREEN}服务已停止${NC}"
}

# 重启服务
restart_services() {
    stop_services
    start_services
}

# 查看日志
view_logs() {
    if [ -n "$1" ]; then
        docker-compose -f "$COMPOSE_FILE" logs -f "$1"
    else
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# 查看状态
view_status() {
    echo -e "${GREEN}AICG 平台服务状态:${NC}"
    docker-compose -f "$COMPOSE_FILE" ps
}

# 构建镜像
build_images() {
    check_env
    echo -e "${GREEN}构建 AICG 平台镜像...${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" build --no-cache
    echo -e "${GREEN}镜像构建完成!${NC}"
}

# 运行数据库迁移
run_migrate() {
    check_env
    echo -e "${GREEN}运行数据库迁移...${NC}"
    docker-compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec backend alembic upgrade head
    echo -e "${GREEN}迁移完成!${NC}"
}

# 清理资源
clean_resources() {
    echo -e "${YELLOW}清理 Docker 资源...${NC}"
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    docker system prune -f
    echo -e "${GREEN}清理完成!${NC}"
}

# 进入后端 shell
enter_shell() {
    docker-compose -f "$COMPOSE_FILE" exec backend /bin/bash
}

# 主函数
case "$1" in
    start)
        start_services
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        ;;
    logs)
        view_logs "$2"
        ;;
    status)
        view_status
        ;;
    build)
        build_images
        ;;
    migrate)
        run_migrate
        ;;
    clean)
        clean_resources
        ;;
    shell)
        enter_shell
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        exit 1
        ;;
esac
