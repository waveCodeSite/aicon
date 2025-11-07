# Alembic数据库迁移

这个目录包含AICG内容分发平台的数据库迁移文件。

## 概述

Alembic是SQLAlchemy的数据库迁移工具，用于管理数据库结构的版本控制和变更。

## 文件结构

```
migrations/
├── env.py              # Alembic环境配置
├── script.py.mako      # 迁移文件模板
├── README.md           # 本文件
└── versions/           # 迁移文件目录
    └── __init__.py
```

## 使用指南

### 基本命令

```bash
# 检查当前版本
uv run alembic current

# 查看迁移历史
uv run alembic history

# 查看待执行的迁移
uv run alembic heads

# 创建新迁移（自动生成变更）
uv run alembic revision --autogenerate -m "描述变更内容"

# 执行迁移
uv run alembic upgrade head

# 回滚到上一个版本
uv run alembic downgrade -1

# 回滚到特定版本
uv run alembic downgrade <revision_id>

# 回滚到基础版本
uv run alembic downgrade base
```

### 开发环境

1. **修改模型后创建迁移**:
   ```bash
   uv run alembic revision --autogenerate -m "添加新模型或字段"
   ```

2. **查看生成的迁移文件**:
   编辑 `versions/` 目录下生成的文件，确保变更正确

3. **执行迁移**:
   ```bash
   uv run alembic upgrade head
   ```

### 生产环境

1. **备份数据库**:
   ```bash
   pg_dump -U aicg_user aicg_db > backup_$(date +%Y%m%d_%H%M%S).sql
   ```

2. **测试迁移文件**（可选）:
   ```bash
   uv run alembic upgrade head --sql
   ```

3. **执行迁移**:
   ```bash
   uv run alembic upgrade head
   ```

4. **验证迁移结果**:
   ```bash
   uv run alembic current
   ```

## 迁移文件命名规范

迁移文件按以下格式命名：
```
<revision_id>_<description>.py
```

例如：
```
20241107_120000_add_user_model.py
20241107_130000_add_project_table.py
```

## 最佳实践

### 1. 迁移文件管理

- 每个迁移文件应该只包含一个逻辑变更
- 使用描述性的迁移消息
- 在生成后检查迁移文件内容
- 不要修改已发布的迁移文件

### 2. 数据安全

- 在生产环境执行迁移前备份数据库
- 在迁移包含大量数据变更时，考虑分阶段执行
- 测试迁移的回滚操作

### 3. 性能考虑

- 对于大型表，添加索引可能需要较长时间
- 在生产环境考虑使用`--sql`选项预览SQL
- 对于复杂迁移，考虑在低峰期执行

### 4. 团队协作

- 在合并分支前解决迁移冲突
- 保持迁移文件的线性历史
- 及时同步迁移文件到版本控制

## 常见问题

### 1. 迁移失败

如果迁移执行失败，检查：

- 数据库连接是否正常
- 表或字段是否已经存在
- 外键约束是否满足
- 权限是否足够

### 2. 迁移历史不一致

如果发现迁移历史不一致：

```bash
# 标记特定版本为当前版本（谨慎使用）
uv run alembic stamp <revision_id>

# 标记为最新版本
uv run alembic stamp head
```

### 3. 自动生成不准确

如果自动生成不准确：

1. 手动编辑生成的迁移文件
2. 确保所有模型都有正确的表名和字段定义
3. 检查关系和约束的定义

## 环境配置

Alembic使用以下配置：

- **数据库URL**: 从环境变量或配置文件读取
- **日志配置**: 使用标准的Python日志配置
- **模型导入**: 自动导入`src.models`中的所有模型

## 故障排除

### 检查迁移状态

```bash
# 查看当前数据库状态
uv run alembic current

# 查看所有迁移历史
uv run alembic history

# 查看未应用的迁移
uv run alembic heads
```

### 重置数据库（仅开发环境）

```bash
# 删除所有表
uv run alembic downgrade base

# 重新创建所有表
uv run alembic upgrade head
```

### 手动SQL执行

对于复杂情况，可以直接执行SQL：

```bash
# 连接到数据库
psql -U aicg_user -d aicg_db

# 手动执行SQL
```

## 相关文档

- [Alembic官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy文档](https://docs.sqlalchemy.org/)
- [PostgreSQL文档](https://www.postgresql.org/docs/)