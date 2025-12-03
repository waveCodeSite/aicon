"""add video_task table

Revision ID: 006
Revises: 005
Create Date: 2025-12-03 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """创建video_tasks表"""
    op.create_table(
        'video_tasks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, comment='主键ID'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, comment='创建时间'),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, comment='更新时间'),
        
        # 关联字段
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, comment='用户ID（外键索引，无约束）'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, comment='项目ID（外键索引，无约束）'),
        sa.Column('chapter_id', postgresql.UUID(as_uuid=True), nullable=False, index=True, comment='章节ID（外键索引，无约束）'),
        sa.Column('api_key_id', postgresql.UUID(as_uuid=True), nullable=True, index=True, comment='API密钥ID（可选）'),
        sa.Column('background_id', postgresql.UUID(as_uuid=True), nullable=True, comment='背景音乐/图片ID（可选）'),
        
        # 生成设置
        sa.Column('gen_setting', sa.Text, nullable=True, comment='生成设置（JSON格式）'),
        
        # 处理状态
        sa.Column('status', sa.String(30), nullable=False, server_default='pending', index=True, comment='任务状态'),
        sa.Column('progress', sa.Integer, nullable=False, server_default='0', comment='处理进度（0-100）'),
        sa.Column('current_sentence_index', sa.Integer, nullable=True, comment='当前处理的句子索引（用于断点续传）'),
        sa.Column('total_sentences', sa.Integer, nullable=True, comment='总句子数量'),
        
        # 生成结果
        sa.Column('video_key', sa.String(500), nullable=True, comment='MinIO对象键（存储路径）'),
        sa.Column('video_url', sa.String(500), nullable=True, comment='视频预签名URL（按需生成）'),
        sa.Column('video_duration', sa.Integer, nullable=True, comment='视频时长（秒）'),
        
        # 错误信息
        sa.Column('error_message', sa.Text, nullable=True, comment='错误信息'),
        sa.Column('error_sentence_id', postgresql.UUID(as_uuid=True), nullable=True, comment='出错的句子ID（用于调试）'),
        
        comment='视频任务表 - 视频生成任务管理'
    )
    
    # 创建索引
    op.create_index('idx_video_task_user', 'video_tasks', ['user_id'])
    op.create_index('idx_video_task_project', 'video_tasks', ['project_id'])
    op.create_index('idx_video_task_chapter', 'video_tasks', ['chapter_id'])
    op.create_index('idx_video_task_status', 'video_tasks', ['status'])
    op.create_index('idx_video_task_created', 'video_tasks', ['created_at'])


def downgrade() -> None:
    """删除video_tasks表"""
    op.drop_index('idx_video_task_created', table_name='video_tasks')
    op.drop_index('idx_video_task_status', table_name='video_tasks')
    op.drop_index('idx_video_task_chapter', table_name='video_tasks')
    op.drop_index('idx_video_task_project', table_name='video_tasks')
    op.drop_index('idx_video_task_user', table_name='video_tasks')
    op.drop_table('video_tasks')
