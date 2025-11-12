<template>
  <div class="project-detail-page">
    <!-- 页面头部信息 -->
    <div class="page-header">
      <h1 class="page-title">{{ project?.title || '项目详情' }}</h1>
      <p class="page-description">查看和管理项目的详细信息</p>
    </div>

    <!-- 操作按钮 -->
    <template #actions>
      <el-button @click="editProject" :icon="Edit">
        编辑项目
      </el-button>
      <el-button type="primary" @click="downloadFile" :icon="Download">
        下载文件
      </el-button>
    </template>

    <div v-if="project" class="project-content">
      <!-- 项目概览 -->
      <el-row :gutter="24">
        <el-col :span="16">
          <el-card class="project-overview">
            <template #header>
              <h3>项目概览</h3>
            </template>

            <div class="overview-content">
              <div class="project-info">
                <div class="info-item">
                  <span class="label">项目名称:</span>
                  <span class="value">{{ project.title }}</span>
                </div>
                <div class="info-item">
                  <span class="label">创建时间:</span>
                  <span class="value">{{ formatDate(project.created_at) }}</span>
                </div>
                <div class="info-item">
                  <span class="label">更新时间:</span>
                  <span class="value">{{ formatDate(project.updated_at) }}</span>
                </div>
                <div class="info-item">
                  <span class="label">状态:</span>
                  <el-tag :type="project.status === 'completed' ? 'success' : 'warning'">
                    {{ project.status === 'completed' ? '已完成' : '进行中' }}
                  </el-tag>
                </div>
                <div class="info-item" v-if="project.file_type">
                  <span class="label">文件类型:</span>
                  <span class="value">{{ project.file_type.toUpperCase() }}</span>
                </div>
                <div class="info-item" v-if="project.file_size">
                  <span class="label">文件大小:</span>
                  <span class="value">{{ formatFileSize(project.file_size) }}</span>
                </div>
              </div>

              <div class="project-description" v-if="project.description">
                <h4>项目描述</h4>
                <p>{{ project.description }}</p>
              </div>
            </div>
          </el-card>

          <!-- 文件信息 -->
          <el-card class="file-info" v-if="project.minio_object_key">
            <template #header>
              <h3>文件信息</h3>
            </template>

            <div class="file-details">
              <div class="file-item">
                <span class="label">原始文件名:</span>
                <span class="value">{{ project.original_filename }}</span>
              </div>
              <div class="file-item">
                <span class="label">处理状态:</span>
                <el-tag :type="getProcessingStatusType(project.file_processing_status)">
                  {{ getProcessingStatusText(project.file_processing_status) }}
                </el-tag>
              </div>
              <div class="file-item" v-if="project.processing_progress !== undefined">
                <span class="label">处理进度:</span>
                <el-progress :percentage="project.processing_progress" :status="project.processing_progress === 100 ? 'success' : ''" />
              </div>
            </div>

            <div class="file-actions" v-if="project.minio_object_key">
              <el-button type="primary" @click="downloadFile">
                <el-icon><Download /></el-icon>
                下载文件
              </el-button>
              <el-button @click="previewFile">
                <el-icon><View /></el-icon>
                预览文件
              </el-button>
            </div>
          </el-card>

          <!-- 处理结果 -->
          <el-card class="processing-results" v-if="project.file_processing_status === 'completed'">
            <template #header>
              <h3>处理结果</h3>
            </template>

            <div class="results-grid">
              <div class="result-item">
                <div class="result-icon words">
                  <el-icon><Document /></el-icon>
                </div>
                <div class="result-content">
                  <div class="result-value">{{ project.word_count || 0 }}</div>
                  <div class="result-label">字数统计</div>
                </div>
              </div>

              <div class="result-item">
                <div class="result-icon paragraphs">
                  <el-icon><Reading /></el-icon>
                </div>
                <div class="result-content">
                  <div class="result-value">{{ project.total_paragraphs || 0 }}</div>
                  <div class="result-label">段落数量</div>
                </div>
              </div>

              <div class="result-item">
                <div class="result-icon sentences">
                  <el-icon><ChatLineSquare /></el-icon>
                </div>
                <div class="result-content">
                  <div class="result-value">{{ project.total_sentences || 0 }}</div>
                  <div class="result-label">句子数量</div>
                </div>
              </div>

              <div class="result-item" v-if="project.total_chapters">
                <div class="result-icon chapters">
                  <el-icon><Collection /></el-icon>
                </div>
                <div class="result-content">
                  <div class="result-value">{{ project.total_chapters }}</div>
                  <div class="result-label">章节数量</div>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>

        <el-col :span="8">
          <!-- 项目设置 -->
          <el-card class="project-settings">
            <template #header>
              <h3>项目设置</h3>
            </template>

            <el-form :model="settingsForm" label-width="120px">
              <el-form-item label="项目名称">
                <el-input v-model="settingsForm.title" />
              </el-form-item>
              <el-form-item label="项目描述">
                <el-input v-model="settingsForm.description" type="textarea" rows="4" />
              </el-form-item>
              <el-form-item label="项目状态">
                <el-select v-model="settingsForm.status">
                  <el-option label="进行中" value="active" />
                  <el-option label="已完成" value="completed" />
                  <el-option label="已暂停" value="paused" />
                </el-select>
              </el-form-item>
            </el-form>

            <div class="form-actions">
              <el-button type="primary" @click="saveSettings">
                保存设置
              </el-button>
              <el-button @click="deleteProject" type="danger">
                删除项目
              </el-button>
            </div>
          </el-card>

          <!-- 快捷操作 -->
          <el-card class="quick-actions">
            <template #header>
              <h3>快捷操作</h3>
            </template>

            <div class="action-buttons">
              <el-button type="primary" @click="startProcessing" :disabled="project.file_processing_status === 'processing'">
                <el-icon><VideoPlay /></el-icon>
                开始处理
              </el-button>
              <el-button @click="exportProject">
                <el-icon><Download /></el-icon>
                导出项目
              </el-button>
              <el-button @click="shareProject">
                <el-icon><Share /></el-icon>
                分享项目
              </el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <div v-else class="loading-state">
      <el-skeleton :rows="5" animated />
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  Document,
  Reading,
  ChatLineSquare,
  Collection,
  VideoPlay,
  Download,
  Share,
  View,
  Edit
} from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()

const project = ref(null)
const settingsForm = reactive({
  title: '',
  description: '',
  status: 'active'
})

const formatDate = (dateString) => {
  if (!dateString) return '未知'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const getProcessingStatusType = (status) => {
  const statusTypes = {
    'uploaded': 'info',
    'processing': 'warning',
    'completed': 'success',
    'failed': 'danger'
  }
  return statusTypes[status] || 'info'
}

const getProcessingStatusText = (status) => {
  const statusTexts = {
    'uploaded': '已上传',
    'processing': '处理中',
    'completed': '处理完成',
    'failed': '处理失败'
  }
  return statusTexts[status] || '未知'
}

const saveSettings = () => {
  // 模拟保存设置 (实际应该调用API)
  Object.assign(project.value, settingsForm)
  project.value.updated_at = new Date().toISOString()
  ElMessage.success('设置保存成功')
}

const deleteProject = async () => {
  try {
    await ElMessageBox.confirm(
      '确定要删除这个项目吗？此操作不可撤销。',
      '删除确认',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    ElMessage.success('项目已删除')
    router.push('/projects')
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除项目失败:', error)
    }
  }
}

const downloadFile = () => {
  if (project.value.minio_object_key) {
    // 实际应该调用文件下载API
    ElMessage.info('开始下载文件...')
  }
}

const previewFile = () => {
  if (project.value.minio_object_key) {
    // 实际应该打开文件预览
    ElMessage.info('文件预览功能开发中...')
  }
}

const startProcessing = () => {
  // 实际应该调用文件处理API
  ElMessage.info('开始处理文件...')
}

const exportProject = () => {
  ElMessage.info('导出功能开发中...')
}

const shareProject = () => {
  ElMessage.info('分享功能开发中...')
}

const editProject = () => {
  ElMessage.info('编辑功能开发中...')
}

onMounted(async () => {
  // 模拟加载项目数据 (实际应该从API获取)
  const projectId = route.params.id
  if (projectId) {
    try {
      // 模拟API调用
      const mockProject = {
        id: projectId,
        title: '示例项目',
        description: '这是一个示例项目，展示了文档上传和项目管理功能',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        status: 'active',
        file_type: 'txt',
        file_size: 1024 * 10, // 10KB
        original_filename: 'example.txt',
        minio_bucket: 'test-bucket',
        minio_object_key: `uploads/user-${projectId}/example.txt`,
        file_processing_status: 'completed',
        processing_progress: 100,
        word_count: 150,
        total_paragraphs: 5,
        total_sentences: 8,
        total_chapters: 3
      }

      project.value = mockProject
      Object.assign(settingsForm, {
        title: project.value.title,
        description: project.value.description,
        status: project.value.status
      })
    } catch (error) {
      console.error('加载项目失败:', error)
      ElMessage.error('加载项目失败')
    }
  }
})
</script>

<style scoped>
.project-detail-page {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.page-header {
  display: flex;
  flex-direction: column;
  gap: var(--space-xs);
}

.page-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0;
  line-height: 1.2;
}

.page-description {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

.project-content {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.project-overview,
.project-settings,
.quick-actions,
.file-info,
.processing-results {
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-sm);
  margin-bottom: var(--space-xl);
}

.project-overview :deep(.el-card__header),
.project-settings :deep(.el-card__header),
.quick-actions :deep(.el-card__header),
.file-info :deep(.el-card__header),
.processing-results :deep(.el-card__header) {
  font-weight: 600;
}

.overview-content {
  padding: var(--space-lg) 0;
}

.project-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.info-item,
.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) 0;
  border-bottom: 1px solid var(--border-primary);
}

.info-item:last-child,
.file-item:last-child {
  border-bottom: none;
}

.info-item .label,
.file-item .label {
  font-weight: 600;
  color: var(--text-secondary);
}

.info-item .value,
.file-item .value {
  color: var(--text-primary);
}

.project-description h4 {
  margin: 0 0 var(--space-md) 0;
  font-size: var(--text-lg);
  font-weight: 600;
  color: var(--text-primary);
}

.project-description p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

.file-details {
  margin-bottom: var(--space-lg);
}

.file-actions {
  display: flex;
  gap: var(--space-md);
}

.form-actions {
  display: flex;
  gap: var(--space-md);
  margin-top: var(--space-xl);
}

.results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: var(--space-lg);
}

.result-item {
  display: flex;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  transition: all var(--transition-base);
}

.result-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.result-icon {
  width: 48px;
  height: 48px;
  border-radius: var(--radius-lg);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
}

.result-icon.words {
  background: linear-gradient(135deg, #667eea, #764ba2);
}

.result-icon.paragraphs {
  background: linear-gradient(135deg, #f093fb, #f5576c);
}

.result-icon.sentences {
  background: linear-gradient(135deg, #4facfe, #00f2fe);
}

.result-icon.chapters {
  background: linear-gradient(135deg, #fa709a, #fee140);
}

.result-content {
  flex: 1;
}

.result-value {
  font-size: var(--text-xl);
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1;
  margin-bottom: var(--space-xs);
}

.result-label {
  font-size: var(--text-sm);
  color: var(--text-secondary);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
}

.action-buttons .el-button {
  justify-content: flex-start;
}

.loading-state {
  padding: var(--space-2xl);
}

@media (max-width: 768px) {

  .project-info,
  .results-grid {
    grid-template-columns: 1fr;
  }

  .form-actions,
  .file-actions {
    flex-direction: column;
  }

  .action-buttons {
    gap: var(--space-sm);
  }
}
</style>