"""添加存储配置

Revision ID: 011
Revises: 010
Create Date: 2024-12-07 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011'
down_revision = '010'
branch_labels = None
depends_on = None


def upgrade():
    """添加存储配置到系统设置"""
    # 插入默认存储配置（使用JSON格式存储）
    op.execute("""
        INSERT INTO system_settings (id, key, value, description)
        VALUES (
            gen_random_uuid(),
            'storage_config',
            '{"provider": "minio", "endpoint": "localhost:9000", "access_key": "minioadmin", "secret_key": "minioadmin", "bucket": "aicg-files", "region": "us-east-1", "secure": false}',
            '对象存储配置'
        )
        ON CONFLICT (key) DO NOTHING
    """)


def downgrade():
    """删除存储配置"""
    op.execute("DELETE FROM system_settings WHERE key = 'storage_config'")
