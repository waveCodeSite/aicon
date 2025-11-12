<template>
  <div class="project-detail">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="8" animated />
    </div>

    <!-- 项目详情内容 -->
    <div v-else-if="project" class="detail-content">
      <!-- 头部操作栏 -->
      <div class="detail-header">
        <div class="header-left">
          <el-button :icon="ArrowLeft" @click="handleBack">
            返回
          </el-button>
          <div class="breadcrumb">
            <el-breadcrumb separator="/">
              <el-breadcrumb-item @click="handleBack">项目列表</el-breadcrumb-item>
              <el-breadcrumb-item>{{ project.title }}</el-breadcrumb-item>
            </el-breadcrumb>
          </div>
        </div>

        <div class="header-actions">
          <el-button-group>
            <el-button
              :icon="Edit"
              @click="handleEdit"
            >
              编辑
            </el-button>
            <el-button
              :icon="Download"
              @click="handleDownload"
            >
              下载
            </el-button>
            <el-dropdown @command="handleCommand">
              <el-button :icon="More">
                更多
              </el-button>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item
                    :command="`duplicate:${project.id}`"
                    :icon="CopyDocument"
                  >
                    复制项目
                  </el-dropdown-item>
                  <el-dropdown-item
                    :command="`archive:${project.id}`"
                    :icon="FolderOpened"
                    :disabled="project.status === 'archived'"
                  >
                    {{ project.status === 'archived' ? '已归档' : '归档' }}
                  </el-dropdown-item>
                  <!-- 重新处理功能暂未实现 -->
                  <el-dropdown-item :command="`reprocess:${project.id}`" :icon="Refresh" disabled>
                    重新处理
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
          </el-button-group>
        </div>
      </div>

      <!-- 项目基本信息 -->
      <el-card class="info-card">
        <template #header>
          <div class="card-header">
            <h2 class="card-title">{{ project.title }}</h2>
            <div class="status-tags">
              <el-tag :type="getStatusType(project.status)" effect="plain">
                {{ getStatusText(project.status) }}
              </el-tag>
              <!-- 文件状态已合并到主状态标签中 -->
              <el-tag v-if="project.is_public" type="info" effect="plain">
                公开
              </el-tag>
            </div>
          </div>
        </template>

        <el-row :gutter="24">
          <!-- 左侧信息 -->
          <el-col :span="16">
            <div class="project-description">
              <h3>项目描述</h3>
              <p>{{ project.description || '暂无描述' }}</p>
            </div>

            <!-- 文件信息 -->
            <div class="file-info-section">
              <h3>文件信息</h3>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="原始文件名">
                  {{ project.original_filename || '-' }}
                </el-descriptions-item>
                <el-descriptions-item label="文件类型">
                  {{ getFileTypeText(project.file_type) }}
                </el-descriptions-item>
                <el-descriptions-item label="文件大小">
                  {{ formatFileSize(project.file_size) }}
                </el-descriptions-item>
                <el-descriptions-item label="文件格式">
                  {{ project.file_extension?.toUpperCase() || '-' }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 内容统计 -->
            <div class="content-stats">
              <h3>内容统计</h3>
              <el-row :gutter="16">
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ formatNumber(project.word_count) }}</div>
                    <div class="stat-label">总字数</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ formatNumber(project.paragraph_count) }}</div>
                    <div class="stat-label">段落数</div>
                  </div>
                </el-col>
                <el-col :span="6">
                  <div class="stat-item">
                    <div class="stat-value">{{ formatNumber(project.sentence_count) }}</div>
                    <div class="stat-label">句子数</div>
                  </div>
                </el-col>
                <el-col :span="6" v-if="project.chapter_count > 0">
                  <div class="stat-item">
                    <div class="stat-value">{{ formatNumber(project.chapter_count) }}</div>
                    <div class="stat-label">章节数</div>
                  </div>
                </el-col>
              </el-row>
            </div>
          </el-col>

          <!-- 右侧信息 -->
          <el-col :span="8">
            <!-- 处理进度 -->
            <div v-if="project.status === 'parsing' || project.status === 'generating'" class="progress-card">
              <h3>处理进度</h3>
              <el-progress
                type="circle"
                :percentage="project.processing_progress || 0"
                :width="120"
                :stroke-width="8"
              />
              <div class="progress-text">
                {{ Math.round(project.processing_progress || 0) }}% 完成
              </div>
            </div>

            <!-- 时间信息 -->
            <div class="time-info">
              <h3>时间信息</h3>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="创建时间">
                  {{ formatDateTime(project.created_at) }}
                </el-descriptions-item>
                <el-descriptions-item label="更新时间">
                  {{ formatDateTime(project.updated_at) }}
                </el-descriptions-item>
                <el-descriptions-item v-if="project.processed_at" label="处理完成时间">
                  {{ formatDateTime(project.processed_at) }}
                </el-descriptions-item>
              </el-descriptions>
            </div>

            <!-- 项目元数据 -->
            <div class="metadata-section">
              <h3>项目元数据</h3>
              <el-descriptions :column="1" border size="small">
                <el-descriptions-item label="项目ID">
                  <el-text type="info" size="small">{{ project.id }}</el-text>
                </el-descriptions-item>
                <el-descriptions-item label="存储对象键" v-if="project.minio_object_key">
                  <el-text type="info" size="small" class="object-key">
                    {{ project.minio_object_key }}
                  </el-text>
                </el-descriptions-item>
                <el-descriptions-item label="文件哈希" v-if="project.file_hash">
                  <el-text type="info" size="small">{{ project.file_hash }}</el-text>
                </el-descriptions-item>
              </el-descriptions>
            </div>
          </el-col>
        </el-row>
      </el-card>

      <!-- 操作按钮组 -->
      <div class="action-buttons">
        <el-button type="primary" :icon="VideoPlay" @click="handleStartGeneration">
          开始视频生成
        </el-button>
        <el-button :icon="Document" @click="handleViewContent">
          查看文件内容
        </el-button>
        <el-button :icon="Refresh" @click="handleRefresh" :loading="refreshing">
          刷新数据
        </el-button>
      </div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="error-state">
      <el-result
        icon="error"
        title="加载失败"
        :sub-title="error"
      >
        <template #extra>
          <el-button type="primary" @click="handleRefresh">
            重新加载
          </el-button>
          <el-button @click="handleBack">
            返回列表
          </el-button>
        </template>
      </el-result>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  ArrowLeft,
  Edit,
  Download,
  Delete,
  More,
  CopyDocument,
  FolderOpened,
  Refresh,
  VideoPlay,
  Document
} from '@element-plus/icons-vue'

// Props定义
const props = defineProps({
  projectId: {
    type: String,
    required: true
  },
  project: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  error: {
    type: String,
    default: null
  }
})

// Emits定义
const emit = defineEmits([
  'back',
  'edit',
  'delete',
  'download',
  'duplicate',
  'archive',
  'reprocess',
  'refresh',
  'start-generation',
  'view-content'
])

// 响应式数据
const refreshing = ref(false)

// 方法
const handleBack = () => {
  emit('back')
}

const handleEdit = () => {
  emit('edit', props.project)
}

const handleDownload = () => {
  emit('download', props.project)
}

const handleCommand = async (command) => {
  const [action, projectId] = command.split(':')

  switch (action) {
    case 'duplicate':
      await handleDuplicate()
      break
    case 'archive':
      await handleArchive()
      break
    case 'reprocess':
      await handleReprocess()
      break
    case 'delete':
      await handleDelete()
      break
  }
}

const handleDuplicate = async () => {
  try {
    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要复制项目 "${props.project.title}" 吗？`,
      '确认复制',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info'
      }
    )

    if (confirmed) {
      emit('duplicate', props.project)
      ElMessage.success('项目复制请求已发送')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleArchive = async () => {
  try {
    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要${props.project.status === 'archived' ? '取消归档' : '归档'}项目 "${props.project.title}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (confirmed) {
      emit('archive', props.project)
      ElMessage.success(props.project.status === 'archived' ? '取消归档成功' : '归档成功')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleReprocess = async () => {
  try {
    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要重新处理项目 "${props.project.title}" 的文件吗？`,
      '确认重新处理',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    if (confirmed) {
      emit('reprocess', props.project)
      ElMessage.success('重新处理请求已发送')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleDelete = async () => {
  try {
    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要删除项目 "${props.project.title}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger'
      }
    )

    if (confirmed) {
      emit('delete', props.project)
      ElMessage.success('项目删除成功')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleStartGeneration = () => {
  if (!['completed', 'parsed'].includes(props.project.status)) {
    ElMessage.warning('文件处理完成后才能开始视频生成')
    return
  }
  emit('start-generation', props.project)
}

const handleViewContent = () => {
  emit('view-content', props.project)
}

const handleRefresh = async () => {
  refreshing.value = true
  try {
    emit('refresh', props.projectId)
  } finally {
    setTimeout(() => {
      refreshing.value = false
    }, 1000)
  }
}

// 工具方法
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

const getFileTypeText = (fileType) => {
  const textMap = {
    txt: 'TXT文档',
    md: 'Markdown文档',
    docx: 'Word文档',
    epub: 'EPUB电子书'
  }
  return textMap[fileType] || '未知文件类型'
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
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}
</script>

<style scoped>
.project-detail {
  min-height: 100%;
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

.loading-container {
  padding: var(--space-xl);
}

.detail-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-xl);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
  padding: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.breadcrumb {
  display: none;
}

@media (min-width: 768px) {
  .breadcrumb {
    display: block;
  }
}

.header-actions {
  display: flex;
  gap: var(--space-sm);
}

/* 卡片样式优化 */
:deep(.el-card) {
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  background: var(--bg-primary);
}

:deep(.el-card__header) {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.02), rgba(139, 92, 246, 0.02));
  border-bottom: 1px solid var(--border-primary);
  padding: var(--space-xl);
}

:deep(.el-card__body) {
  padding: var(--space-xl);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.card-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.2;
  display: flex;
  align-items: center;
  gap: var(--space-md);
}

.status-tags {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  flex-wrap: wrap;
}

/* 内容区块样式 */
.project-description,
.file-info-section,
.content-stats {
  margin-bottom: var(--space-xl);
}

.project-description h3,
.file-info-section h3,
.content-stats h3 {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.project-description h3::before,
.file-info-section h3::before,
.content-stats h3::before {
  content: '';
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, var(--primary-color), var(--primary-hover));
  border-radius: var(--radius-sm);
}

.project-description p {
  color: var(--text-secondary);
  line-height: 1.6;
  margin: 0;
  padding: var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border-left: 3px solid var(--primary-color);
}

/* 统计信息样式 */
.stat-item {
  text-align: center;
  padding: var(--space-lg);
  background: linear-gradient(135deg, var(--bg-secondary), var(--bg-primary));
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  transition: all var(--transition-base);
  position: relative;
  overflow: hidden;
}

.stat-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-color), var(--secondary-color));
  transform: scaleX(0);
  transition: transform var(--transition-base);
}

.stat-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--primary-color);
}

.stat-item:hover::before {
  transform: scaleX(1);
}

.stat-value {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--primary-color);
  margin-bottom: var(--space-sm);
  line-height: 1;
}

.stat-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

/* 进度卡片样式 */
.progress-card {
  padding: var(--space-lg);
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.05), rgba(139, 92, 246, 0.05));
  border-radius: var(--radius-lg);
  border: 1px solid rgba(99, 102, 241, 0.2);
  text-align: center;
  margin-bottom: var(--space-xl);
  position: relative;
}

.progress-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: linear-gradient(90deg, var(--primary-color), var(--primary-hover));
}

.progress-card h3 {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-lg) 0;
}

.progress-text {
  margin-top: var(--space-md);
  font-size: var(--text-base);
  color: var(--text-secondary);
  font-weight: 600;
}

/* 信息区块样式 */
.time-info,
.metadata-section {
  margin-bottom: var(--space-xl);
}

.time-info h3,
.metadata-section h3 {
  font-size: var(--text-lg);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.time-info h3::before,
.metadata-section h3::before {
  content: '';
  width: 4px;
  height: 20px;
  background: linear-gradient(180deg, var(--primary-color), var(--primary-hover));
  border-radius: var(--radius-sm);
}

/* 描述列表样式 */
:deep(.el-descriptions) {
  --el-descriptions-table-border: 1px solid var(--border-primary);
  --el-descriptions-item-bordered-background: var(--bg-secondary);
}

:deep(.el-descriptions__label) {
  font-weight: 600;
  color: var(--text-primary);
  background: var(--bg-secondary);
}

:deep(.el-descriptions__content) {
  color: var(--text-secondary);
}

.object-key {
  word-break: break-all;
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: var(--text-xs);
}

/* 操作按钮样式 */
.action-buttons {
  display: flex;
  gap: var(--space-md);
  justify-content: center;
  align-items: center;
  padding: var(--space-xl) 0;
}

.action-buttons .el-button {
  border-radius: var(--radius-lg);
  font-weight: 600;
  padding: var(--space-md) var(--space-xl);
  transition: all var(--transition-base);
  min-width: 120px;
}

.action-buttons .el-button--primary {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border: none;
  box-shadow: var(--shadow-md);
}

.action-buttons .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg), 0 10px 25px rgba(99, 102, 241, 0.3);
}

.action-buttons .el-button--default {
  border-color: var(--border-primary);
  background: var(--bg-secondary);
  color: var(--text-primary);
}

.action-buttons .el-button--default:hover {
  border-color: var(--primary-color);
  background: rgba(99, 102, 241, 0.05);
  transform: translateY(-1px);
}

/* 错误状态样式 */
.error-state {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 400px;
  padding: var(--space-xl);
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  .stat-item {
    background: linear-gradient(135deg, var(--bg-dark), var(--bg-secondary));
  }

  .progress-card {
    background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(139, 92, 246, 0.1));
    border-color: rgba(99, 102, 241, 0.3);
  }

  .project-description p {
    background: var(--bg-dark);
    border-left-color: var(--primary-color);
  }

  :deep(.el-descriptions) {
    --el-descriptions-table-border: 1px solid var(--border-primary);
    --el-descriptions-item-bordered-background: var(--bg-dark);
  }

  :deep(.el-descriptions__label) {
    background: var(--bg-dark);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .detail-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
    margin-bottom: var(--space-lg);
  }

  .header-left {
    width: 100%;
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-sm);
  }

  .header-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .card-title {
    font-size: var(--text-xl);
  }

  :deep(.el-card__header) {
    padding: var(--space-lg);
  }

  :deep(.el-card__body) {
    padding: var(--space-lg);
  }

  .stat-item {
    padding: var(--space-md);
  }

  .stat-value {
    font-size: var(--text-xl);
  }

  .action-buttons {
    flex-direction: column;
    width: 100%;
  }

  .action-buttons .el-button {
    width: 100%;
  }

  .object-key {
    font-size: 10px;
  }
}

@media (max-width: 480px) {
  .project-detail {
    gap: var(--space-lg);
  }

  .card-title {
    font-size: var(--text-lg);
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }

  .status-tags {
    flex-wrap: wrap;
  }

  .stat-item {
    padding: var(--space-sm);
  }

  .stat-value {
    font-size: var(--text-lg);
  }

  .stat-label {
    font-size: var(--text-xs);
  }
}
</style>