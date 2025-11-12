<template>
  <div class="project-card" @click="$emit('view', project)">
    <!-- 卡片头部 -->
    <div class="card-header">
      <div class="file-icon">
        <el-icon :size="32" :color="getFileTypeColor(project.file_type)">
          <component :is="getFileTypeIcon(project.file_type)" />
        </el-icon>
      </div>

      <div class="card-actions">
        <el-dropdown @command="handleCommand" trigger="click" @click.stop>
          <el-button type="text" size="small" :icon="More" />
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item :command="`view:${project.id}`" :icon="View">
                查看详情
              </el-dropdown-item>
              <el-dropdown-item :command="`edit:${project.id}`" :icon="Edit">
                编辑项目
              </el-dropdown-item>
              <el-dropdown-item :command="`download:${project.id}`" :icon="Download">
                下载文件
              </el-dropdown-item>
              <el-dropdown-item :command="`duplicate:${project.id}`" :icon="CopyDocument">
                复制项目
              </el-dropdown-item>
              <!-- 归档功能暂未实现 -->
              <el-dropdown-item :command="`archive:${project.id}`" :icon="FolderOpened" disabled>
                归档项目
              </el-dropdown-item>
              <el-dropdown-item
                :command="`delete:${project.id}`"
                :icon="Delete"
                divided
                danger
              >
                删除项目
              </el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </div>

    <!-- 卡片内容 -->
    <div class="card-content">
      <h3 class="project-title" :title="project.title">
        {{ project.title }}
      </h3>

      <p class="project-description" :title="project.description">
        {{ project.description || '暂无描述' }}
      </p>

      <!-- 文件信息 -->
      <div class="file-info">
        <div class="info-item">
          <el-text size="small" type="info">
            {{ getFileTypeText(project.file_type) }}
          </el-text>
          <el-text size="small" type="info">
            {{ formatFileSize(project.file_size) }}
          </el-text>
          <el-text size="small" type="info" v-if="project.file_hash">
            已验证
          </el-text>
        </div>
      </div>

      <!-- 统计信息 -->
      <div class="stats-info">
        <div class="stat-item">
          <el-text size="small">{{ formatNumber(project.word_count) }}</el-text>
          <el-text size="small" type="info">字数</el-text>
        </div>
        <div class="stat-item">
          <el-text size="small">{{ formatNumber(project.paragraph_count) }}</el-text>
          <el-text size="small" type="info">段落</el-text>
        </div>
        <div class="stat-item" v-if="project.chapter_count > 0">
          <el-text size="small">{{ formatNumber(project.chapter_count) }}</el-text>
          <el-text size="small" type="info">章节</el-text>
        </div>
      </div>

      <!-- 状态标签 -->
      <div class="status-tags">
        <el-tag
          :type="getStatusType(project.status)"
          size="small"
          effect="plain"
        >
          {{ getStatusText(project.status) }}
        </el-tag>
      </div>

      <!-- 处理进度条 -->
      <div v-if="project.status === 'parsing' || project.status === 'generating'" class="progress-section">
        <el-progress
          :percentage="project.processing_progress || 0"
          :show-text="false"
          :stroke-width="4"
        />
        <el-text size="small" type="info">
          处理进度: {{ Math.round(project.processing_progress || 0) }}%
        </el-text>
      </div>
    </div>

    <!-- 卡片底部 -->
    <div class="card-footer">
      <div class="time-info">
        <el-text size="small" type="info">
          创建于 {{ formatDateTime(project.created_at) }}
        </el-text>
        <el-text size="small" type="info">
          更新于 {{ formatDateTime(project.updated_at) }}
        </el-text>
      </div>

      <div class="action-buttons">
        <el-button
          type="primary"
          size="small"
          @click.stop="$emit('view', project)"
        >
          查看
        </el-button>
        <el-button
          size="small"
          @click.stop="$emit('edit', project)"
        >
          编辑
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import {
  View,
  Edit,
  Download,
  Delete,
  More,
  CopyDocument,
  FolderOpened,
  Document,
  VideoPlay,
  Microphone,
  Picture
} from '@element-plus/icons-vue'

// Props定义
const props = defineProps({
  project: {
    type: Object,
    required: true
  }
})

// Emits定义
const emit = defineEmits([
  'view',
  'edit',
  'delete',
  'download',
  'duplicate',
  'archive'
])

// 计算属性
const getFileTypeIcon = (fileType) => {
  const iconMap = {
    'txt': Document,
    'md': Document,
    'docx': Document,
    'epub': Document,
    'video': VideoPlay,
    'audio': Microphone,
    'image': Picture
  }
  return iconMap[fileType] || Document
}

const getFileTypeColor = (fileType) => {
  const colorMap = {
    'txt': '#606266',
    'md': '#409EFF',
    'docx': '#67C23A',
    'epub': '#E6A23C',
    'video': '#F56C6C',
    'audio': '#909399',
    'image': '#909399'
  }
  return colorMap[fileType] || '#606266'
}

const getFileTypeText = (fileType) => {
  const textMap = {
    'txt': 'TXT',
    'md': 'Markdown',
    'docx': 'Word',
    'epub': 'EPUB',
    'video': '视频',
    'audio': '音频',
    'image': '图片'
  }
  return textMap[fileType] || '未知'
}

// 方法
const handleCommand = (command) => {
  const [action, projectId] = command.split(':')

  switch (action) {
    case 'view':
      emit('view', props.project)
      break
    case 'edit':
      emit('edit', props.project)
      break
    case 'download':
      emit('download', props.project)
      break
    case 'duplicate':
      emit('duplicate', props.project)
      break
    case 'archive':
      emit('archive', props.project)
      break
    case 'delete':
      emit('delete', props.project)
      break
  }
}

const getStatusType = (status) => {
  const typeMap = {
    uploaded: 'info',
    parsing: 'warning',
    parsed: 'success',
    generating: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    uploaded: '已上传',
    parsing: '解析中',
    parsed: '解析完成',
    generating: '生成中',
    completed: '已完成',
    failed: '失败'
  }
  return textMap[status] || status
}

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString()
}

const formatDateTime = (dateTime) => {
  if (!dateTime) return '-'
  const date = new Date(dateTime)
  const now = new Date()
  const diffTime = now - date
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))

  if (diffDays === 0) {
    return date.toLocaleTimeString('zh-CN', {
      hour: '2-digit',
      minute: '2-digit'
    })
  } else if (diffDays === 1) {
    return '昨天'
  } else if (diffDays < 7) {
    return `${diffDays}天前`
  } else {
    return date.toLocaleDateString('zh-CN', {
      month: '2-digit',
      day: '2-digit'
    })
  }
}
</script>

<style scoped>
.project-card {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-sm);
  transition: all var(--transition-base);
  cursor: pointer;
  overflow: hidden;
  height: 420px;
  display: flex;
  flex-direction: column;
  position: relative;
}

.project-card:hover {
  transform: translateY(-4px);
  box-shadow: var(--shadow-lg);
  border-color: var(--primary-color);
}

.project-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
  opacity: 0;
  transition: opacity var(--transition-base);
}

.project-card:hover::before {
  opacity: 1;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-lg) var(--space-lg) var(--space-md);
}

.file-icon {
  width: 56px;
  height: 56px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
  box-shadow: var(--shadow-sm);
  position: relative;
  overflow: hidden;
}

.file-icon::after {
  content: '';
  position: absolute;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.1) 0%, transparent 70%);
  animation: pulse 3s ease-in-out infinite;
}

@keyframes pulse {
  0%, 100% { transform: scale(0.8); opacity: 0.5; }
  50% { transform: scale(1.2); opacity: 0.8; }
}

.card-actions {
  opacity: 0;
  transition: opacity var(--transition-base);
}

.project-card:hover .card-actions {
  opacity: 1;
}

.card-content {
  flex: 1;
  padding: 0 var(--space-lg) var(--space-sm);
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  overflow: hidden;
}

.project-title {
  font-size: var(--text-base);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  word-break: break-word;
  flex-shrink: 0;
}

.project-description {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  line-height: 1.4;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 1;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex-shrink: 0;
}

.file-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
}

.info-item {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
}

.info-item .el-text {
  font-size: var(--text-xs);
  font-weight: 500;
}

.stats-info {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: var(--space-sm);
  padding: var(--space-sm);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  flex-shrink: 0;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.stat-item .el-text:first-child {
  font-size: var(--text-sm);
  font-weight: 700;
  color: var(--primary-color);
  line-height: 1;
}

.stat-item .el-text:last-child {
  font-size: var(--text-xs);
  color: var(--text-secondary);
  margin-top: 1px;
  font-weight: 500;
}

.status-tags {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
}

.progress-section {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.progress-section .el-progress {
  --el-progress-bg-color: var(--bg-secondary);
  --el-progress-border-radius: var(--radius-full);
}

.card-footer {
  padding: var(--space-sm) var(--space-lg) var(--space-md);
  background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.02));
  border-top: 1px solid var(--border-primary);
  margin-top: auto;
  flex-shrink: 0;
}

.time-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-md);
}

.time-info .el-text {
  font-size: var(--text-xs);
  color: var(--text-tertiary);
}

.action-buttons {
  display: flex;
  gap: var(--space-sm);
  justify-content: space-between;
}

.action-buttons .el-button {
  flex: 1;
  border-radius: var(--radius-lg);
  font-weight: 600;
  font-size: var(--text-sm);
  transition: all var(--transition-base);
}

.action-buttons .el-button--primary {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border: none;
  box-shadow: var(--shadow-sm);
}

.action-buttons .el-button--primary:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

.action-buttons .el-button--default {
  border-color: var(--border-primary);
  background: var(--bg-secondary);
}

.action-buttons .el-button--default:hover {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .file-icon {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.2), rgba(139, 92, 246, 0.2));
  }

  .card-footer {
    background: linear-gradient(180deg, transparent, rgba(99, 102, 241, 0.05));
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .project-card {
    height: 340px;
  }

  .file-icon {
    width: 48px;
    height: 48px;
  }

  .card-header {
    padding: var(--space-md) var(--space-md) var(--space-sm);
  }

  .card-content {
    padding: 0 var(--space-md) var(--space-sm);
  }

  .card-footer {
    padding: var(--space-sm) var(--space-md) var(--space-md);
  }

  .stats-info {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--space-sm);
    padding: var(--space-sm);
  }

  .project-title {
    font-size: var(--text-base);
  }

  .action-buttons {
    flex-direction: column;
    gap: var(--space-xs);
  }
}
</style>