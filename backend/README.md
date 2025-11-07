# AICG内容分发平台 - 后端服务

基于FastAPI的异步Web服务，提供AI驱动的长文本到视频转换功能。

## 功能特性

- 🚀 **异步架构**: FastAPI + SQLAlchemy 2.0 + asyncpg
- 📝 **智能解析**: 百万字级文档章节自动识别
- 🎬 **视频生成**: 句子级图片、音频、字幕自动生成
- 🔄 **任务队列**: Celery + Redis高并发处理
- 📊 **实时监控**: WebSocket进度推送 + Prometheus指标
- 🔐 **安全认证**: JWT + 密钥加密存储
- 📱 **多平台分发**: B站、YouTube等平台内容发布

## 技术栈

- **语言**: Python 3.11+
- **Web框架**: FastAPI 0.104+
- **数据库**: PostgreSQL 15+ (主), Redis 7.0 (缓存/队列)
- **ORM**: SQLAlchemy 2.0 (异步)
- **任务队列**: Celery 5.3+
- **对象存储**: MinIO
- **视频处理**: FFmpeg + ffmpeg-python
- **包管理**: uv

## 快速开始

### 1. 安装依赖

```bash
# 安装uv (如果还没有安装)
curl -LsSf https://astral.sh/uv/install.sh | sh

# 同步依赖
uv sync
```

### 2. 环境配置

复制环境配置文件:
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置数据库、Redis、MinIO等信息。

### 3. 数据库迁移

```bash
# 运行迁移
uv run alembic upgrade head
```

### 4. 启动服务

```bash
# 启动API服务
uv run uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# 启动Celery Worker (新终端)
uv run celery -A src.workers.base worker --loglevel=info --concurrency=4

# 启动Celery Beat (新终端)
uv run celery -A src.workers.base beat --loglevel=info
```

### 5. 访问API文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- OpenAPI JSON: http://localhost:8000/openapi.json

## 开发指南

### 代码格式化

```bash
# 格式化代码
uv run black src/ tests/
uv run isort src/ tests/

# 代码检查
uv run flake8 src/ tests/
uv run mypy src/
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行特定类型测试
uv run pytest -m unit
uv run pytest -m integration
uv run pytest -m e2e

# 生成覆盖率报告
uv run pytest --cov=src --cov-report=html
```

### 数据库操作

```bash
# 创建新迁移
uv run alembic revision --autogenerate -m "描述变更内容"

# 执行迁移
uv run alembic upgrade head

# 回滚迁移
uv run alembic downgrade -1

# 查看迁移历史
uv run alembic history
```

### 添加新依赖

```bash
# 添加生产依赖
uv add fastapi sqlalchemy

# 添加开发依赖
uv add --dev pytest black
```

## 项目结构

```
backend/
├── src/                   # 源代码
│   ├── models/           # SQLAlchemy数据模型
│   ├── services/         # 业务逻辑服务
│   ├── api/              # FastAPI路由
│   │   └── v1/          # API v1版本
│   ├── core/            # 核心组件(配置、数据库等)
│   ├── workers/         # Celery任务
│   ├── utils/           # 工具函数
│   └── main.py          # FastAPI应用入口
├── tests/               # 测试代码
│   ├── unit/           # 单元测试
│   ├── integration/    # 集成测试
│   └── contract/       # 合同测试
├── migrations/          # 数据库迁移文件
├── scripts/            # 脚本文件
├── pyproject.toml      # 项目配置
└── README.md          # 项目说明
```

## API文档

### 认证相关

- `POST /api/v1/auth/register` - 用户注册
- `POST /api/v1/auth/login` - 用户登录
- `GET /api/v1/auth/me` - 获取当前用户信息

### 项目管理

- `GET /api/v1/projects` - 获取项目列表
- `POST /api/v1/projects` - 创建新项目
- `GET /api/v1/projects/{id}` - 获取项目详情
- `PUT /api/v1/projects/{id}` - 更新项目
- `DELETE /api/v1/projects/{id}` - 删除项目

### 文件上传

- `POST /api/v1/upload` - 上传文件
- `DELETE /api/v1/files/{id}` - 删除文件

### 章节管理

- `GET /api/v1/chapters` - 获取章节列表
- `PUT /api/v1/chapters/{id}/confirm` - 确认章节
- `POST /api/v1/chapters/{id}/parse` - 解析章节

### 视频生成

- `POST /api/v1/generation/start` - 开始视频生成
- `GET /api/v1/generation/tasks/{id}/progress` - 获取生成进度
- `POST /api/v1/generation/tasks/{id}/pause` - 暂停生成任务
- `POST /api/v1/generation/tasks/{id}/resume` - 继续生成任务
- `POST /api/v1/generation/tasks/{id}/cancel` - 取消生成任务

## 环境变量

### 必需变量

```bash
# 数据库
DATABASE_URL=postgresql+asyncpg://user:password@localhost:5432/aicg_db

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-super-secret-jwt-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 可选变量

```bash
# MinIO
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_SECURE=false
MINIO_BUCKET_NAME=aicg-files

# 日志
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true

# API
API_V1_PREFIX=/api/v1
CORS_ORIGINS=["http://localhost:3000"]

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_WORKER_CONCURRENCY=4
```

## 监控

### 健康检查

- `GET /health` - 基础健康检查
- `GET /health/db` - 数据库连接检查
- `GET /health/redis` - Redis连接检查
- `GET /health/celery` - Celery状态检查

### Prometheus指标

访问 `http://localhost:8000/metrics` 获取Prometheus格式的指标数据。

### 结构化日志

系统使用structlog进行结构化日志记录，支持JSON格式输出，便于日志聚合和分析。

## 部署

### Docker部署

```bash
# 构建镜像
docker build -t aicg-backend .

# 运行容器
docker run -d --name aicg-backend \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql+asyncpg://... \
  -e REDIS_URL=redis://... \
  aicg-backend
```

### 生产环境配置

1. 使用生产级数据库连接池
2. 配置HTTPS和反向代理
3. 设置日志轮转
4. 配置监控告警
5. 设置自动备份

## 故障排除

### 常见问题

1. **数据库连接失败**
   - 检查数据库服务状态
   - 验证连接字符串格式
   - 确认网络连通性

2. **Celery任务不执行**
   - 检查Redis连接
   - 确认Worker进程状态
   - 查看任务队列状态

3. **文件上传失败**
   - 检查MinIO服务状态
   - 验证存储桶权限
   - 确认文件大小限制

### 日志查看

```bash
# 查看应用日志
docker logs -f aicg-backend

# 查看特定组件日志
grep "ERROR" /var/log/aicg/backend.log
```

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 提交代码变更
4. 运行测试确保通过
5. 提交Pull Request

## 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 支持

- 文档: https://docs.aicg-platform.com
- 问题反馈: https://github.com/your-org/aicg-platform/issues
- 邮件: support@aicg-platform.com