"""添加用户管理员字段

Revision ID: 009
Revises: 008
Create Date: 2024-12-05 16:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009'
down_revision = '008'
branch_labels = None
depends_on = None


def upgrade():
    """添加 is_admin 字段"""
    op.add_column('users', sa.Column('is_admin', sa.Boolean, server_default='false', nullable=False, comment='是否管理员'))


def downgrade():
    """回滚：删除 is_admin 字段"""
    op.drop_column('users', 'is_admin')
