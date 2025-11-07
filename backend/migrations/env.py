"""
Alembic环境配置 - 简化版本
"""

import asyncio
import os
# 导入应用配置
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.config import settings
from src.models import *  # 导入所有模型

# 获取Alembic配置对象
config = context.config

# 设置同步数据库URL用于Alembic
if hasattr(settings, 'DATABASE_URL'):
    # 将异步URL转换为同步URL
    sync_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    config.set_main_option("sqlalchemy.url", sync_url)
else:
    # 使用配置文件中的URL
    pass

# 设置日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的MetaData对象以支持'autogenerate'
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """在'离线'模式下运行迁移"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """执行迁移的实际函数"""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在异步上下文中运行迁移"""
    # 使用同步URL创建引擎用于Alembic
    sync_url = config.get_main_option("sqlalchemy.url")

    # 创建同步引擎
    from sqlalchemy import create_engine
    engine = create_engine(sync_url, poolclass=pool.NullPool)

    with engine.connect() as connection:
        do_run_migrations(connection)

    engine.dispose()


def run_migrations_online() -> None:
    """在'在线'模式下运行迁移"""
    asyncio.run(run_async_migrations())


def include_object(object, name, type_, reflected, compare_to):
    """决定是否包含某个对象在迁移中"""
    # 排除某些表
    if type_ == "table" and name in ["alembic_version"]:
        return False
    return True


# 运行迁移
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
