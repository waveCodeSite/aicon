# AICG Platform Backend Dockerfile
# 多阶段构建，优化镜像大小

FROM python:3.11-slim AS builder

WORKDIR /app

# 安装构建依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 安装 uv 包管理器
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# 复制依赖文件和构建所需文件
COPY pyproject.toml uv.lock README.md ./

# 安装依赖（仅安装，不构建 editable）
RUN uv sync --frozen --no-dev --no-editable

# ============================================
# 生产镜像
# ============================================
FROM python:3.11-slim AS production

WORKDIR /app

# 安装运行时依赖
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# 从构建阶段复制 uv 和虚拟环境
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY --from=builder /app/.venv /app/.venv

# 设置环境变量
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 复制应用代码
COPY src/ ./src/
COPY migrations/ ./migrations/
COPY alembic.ini ./

# 创建非 root 用户
RUN groupadd -r aicg && useradd -r -g aicg aicg \
    && chown -R aicg:aicg /app

USER aicg

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

# 启动命令
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
