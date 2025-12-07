"""创建存储源表

Revision ID: 012
Revises: 011
Create Date: 2024-12-07 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

revision = '012'
down_revision = '011'
branch_labels = None
depends_on = None


def upgrade():
    """创建存储源表"""
    op.create_table(
        'storage_sources',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('provider', sa.String(50), nullable=False, server_default='minio'),
        sa.Column('endpoint', sa.String(255), nullable=False),
        sa.Column('access_key', sa.String(255), nullable=False),
        sa.Column('secret_key', sa.Text, nullable=False),
        sa.Column('bucket', sa.String(100), nullable=False),
        sa.Column('region', sa.String(50), server_default='us-east-1'),
        sa.Column('secure', sa.Boolean, server_default='false'),
        sa.Column('is_active', sa.Boolean, server_default='false', index=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # 从旧配置迁移数据
    op.execute("""
        INSERT INTO storage_sources (id, name, provider, endpoint, access_key, secret_key, bucket, region, secure, is_active)
        SELECT
            gen_random_uuid(),
            '默认存储',
            COALESCE((value::json->>'provider')::text, 'minio'),
            COALESCE((value::json->>'endpoint')::text, 'localhost:9000'),
            COALESCE((value::json->>'access_key')::text, 'minioadmin'),
            COALESCE((value::json->>'secret_key')::text, 'minioadmin'),
            COALESCE((value::json->>'bucket')::text, 'aicg-files'),
            COALESCE((value::json->>'region')::text, 'us-east-1'),
            COALESCE((value::json->>'secure')::boolean, false),
            true
        FROM system_settings
        WHERE key = 'storage_config'
        LIMIT 1
    """)


def downgrade():
    """删除存储源表"""
    op.drop_table('storage_sources')
