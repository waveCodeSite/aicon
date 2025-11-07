"""
Alembic环境配置
"""

import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context

# 导入应用配置
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from src.core.config import settings
from src.core.database import Base
from src.models import *  # 导入所有模型

# 获取Alembic配置对象
config = context.config

# 设置数据库URL
config.set_main_option("sqlalchemy.url", settings.database_url_sync)

# 设置日志配置
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 添加模型的MetaData对象以支持'autogenerate'
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """在'离线'模式下运行迁移

    这将配置上下文，只需要一个URL，而不是一个Engine，
    尽管在这里也接受Engine。通过跳过Engine的创建，
    我们甚至不需要DBAPI来可用。

    在这里调用的脚本的context.to_dict中将包含一个
    键'url'，它是传递的URL，而不是Engine。
    """
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
        # 包含表注释
        include_object=include_object,
        # 渲染项目
        render_item=render_item,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """在异步上下文中运行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在'在线'模式下运行迁移

    在这里情况下，我们需要创建一个Engine并将连接
    与上下文关联。
    """
    asyncio.run(run_async_migrations())


def include_object(object, name, type_, reflected, compare_to):
    """决定是否包含某个对象在迁移中"""
    # 排除某些表
    if type_ == "table" and name in ["alembic_version"]:
        return False
    # 排除某些视图
    if type_ == "view" and name.startswith("pg_"):
        return False
    return True


def render_item(type_, obj, autogen_context):
    """自定义渲染数据库项"""
    # 为表添加注释
    if type_ == "table" and hasattr(obj, 'info') and 'comment' in obj.info:
        autogen_context.opts['render_item'].append(obj.info['comment'])

    # 为列添加注释
    if type_ == "column" and hasattr(obj, 'comment') and obj.comment:
        autogen_context.opts['render_item'].append(obj.comment)

    # 默认渲染
    return False


# 运行迁移
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()