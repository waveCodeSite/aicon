"""创建系统设置表

Revision ID: 010
Revises: 009
Create Date: 2024-12-05 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010'
down_revision = '009'
branch_labels = None
depends_on = None


def upgrade():
    """创建系统设置表"""
    op.create_table(
        'system_settings',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('key', sa.String(100), nullable=False),
        sa.Column('value', sa.Text, nullable=True),
        sa.Column('description', sa.String(255), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_system_settings_key', 'system_settings', ['key'], unique=True)

    # 插入默认设置
    op.execute("""
        INSERT INTO system_settings (id, key, value, description)
        VALUES (gen_random_uuid(), 'allow_registration', 'true', '是否允许用户注册')
    """)


def downgrade():
    """删除系统设置表"""
    op.drop_index('idx_system_settings_key', table_name='system_settings')
    op.drop_table('system_settings')
