<template>
  <div class="project-list">
    <!-- 视图切换栏 -->
    <div class="view-header">
      <div class="header-left">
        <span class="project-count">
          共 {{ total }} 个项目
        </span>
      </div>
      <div class="header-right">
        <el-button-group>
          <el-button
            :type="viewMode === 'grid' ? 'primary' : 'default'"
            @click="viewMode = 'grid'"
            title="网格视图"
          >
            <el-icon><Grid /></el-icon>
          </el-button>
          <el-button
            :type="viewMode === 'list' ? 'primary' : 'default'"
            @click="viewMode = 'list'"
            title="列表视图"
          >
            <el-icon><List /></el-icon>
          </el-button>
        </el-button-group>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <el-skeleton :rows="5" animated />
    </div>

    <!-- 空状态 -->
    <div v-else-if="!loading && projects.length === 0" class="empty-state">
      <el-empty
        :description="'还没有项目，点击导航栏中的「新建项目」按钮开始吧！'"
        :image-size="120"
      />
    </div>

    <!-- 网格视图 -->
    <div v-else-if="viewMode === 'grid'" class="grid-view">
      <el-row :gutter="20">
        <el-col
          v-for="project in projects"
          :key="project.id"
          :xs="24"
          :sm="12"
          :md="8"
          :lg="6"
          :xl="4"
        >
          <ProjectCard
            :project="project"
            @edit="$emit('edit-project', $event)"
            @delete="$emit('delete-project', $event)"
            @view="$emit('view-project', $event)"
            @download="$emit('download-project', $event)"
          />
        </el-col>
      </el-row>
    </div>

    <!-- 列表视图 -->
    <div v-else class="list-view">
      <el-table
        :data="projects"
        :row-key="(row) => row.id"
        @row-click="handleRowClick"
        stripe
        highlight-current-row
      >
        <el-table-column prop="title" label="项目标题" min-width="200">
          <template #default="{ row }">
            <div class="project-title">
              <el-text class="title-text" truncated>{{ row.title }}</el-text>
              <el-tag
                v-if="row.is_public"
                type="info"
                size="small"
                effect="plain"
              >
                公开
              </el-tag>
            </div>
          </template>
        </el-table-column>

        <el-table-column prop="status" label="状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getStatusType(row.status)"
              size="small"
              effect="plain"
            >
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="file_processing_status" label="文件状态" width="100">
          <template #default="{ row }">
            <el-tag
              :type="getFileStatusType(row.file_processing_status)"
              size="small"
              effect="plain"
            >
              {{ getFileStatusText(row.file_processing_status) }}
            </el-tag>
          </template>
        </el-table-column>

        <el-table-column prop="word_count" label="字数" width="100" align="right">
          <template #default="{ row }">
            <el-text>{{ formatNumber(row.word_count) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="file_size" label="文件大小" width="120" align="right">
          <template #default="{ row }">
            <el-text>{{ formatFileSize(row.file_size) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="created_at" label="创建时间" width="160">
          <template #default="{ row }">
            <el-text>{{ formatDateTime(row.created_at) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column prop="updated_at" label="更新时间" width="160">
          <template #default="{ row }">
            <el-text>{{ formatDateTime(row.updated_at) }}</el-text>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button
                type="primary"
                size="small"
                :icon="View"
                @click.stop="$emit('view-project', row)"
              >
                查看
              </el-button>
              <el-button
                type="default"
                size="small"
                :icon="Edit"
                @click.stop="$emit('edit-project', row)"
              >
                编辑
              </el-button>
              <el-dropdown @command="handleCommand">
                <el-button size="small" :icon="More">
                  更多
                </el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item
                      :command="`download:${row.id}`"
                      :icon="Download"
                    >
                      下载文件
                    </el-dropdown-item>
                    <el-dropdown-item
                      :command="`duplicate:${row.id}`"
                      :icon="CopyDocument"
                    >
                      复制项目
                    </el-dropdown-item>
                    <el-dropdown-item
                      :command="`archive:${row.id}`"
                      :icon="FolderOpened"
                      :disabled="row.status === 'archived'"
                    >
                      {{ row.status === 'archived' ? '已归档' : '归档' }}
                    </el-dropdown-item>
                    <el-dropdown-item
                      :command="`delete:${row.id}`"
                      :icon="Delete"
                      divided
                    >
                      删除项目
                    </el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 分页 -->
    <div v-if="total > 0" class="pagination-container">
      <el-pagination
        :current-page="currentPage"
        :page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        :total="total"
        :background="true"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handlePageChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search,
  Plus,
  Grid,
  List,
  View,
  Edit,
  Download,
  Delete,
  More,
  CopyDocument,
  FolderOpened,
} from '@element-plus/icons-vue'
import ProjectCard from './ProjectCard.vue'

// Props定义
const props = defineProps({
  projects: {
    type: Array,
    default: () => [],
  },
  loading: {
    type: Boolean,
    default: false,
  },
  total: {
    type: Number,
    default: 0,
  },
  currentPage: {
    type: Number,
    default: 1,
  },
  pageSize: {
    type: Number,
    default: 20,
  },
})

// Emits定义
const emit = defineEmits([
  'edit-project',
  'delete-project',
  'view-project',
  'download-project',
  'duplicate-project',
  'archive-project',
  'page-change',
  'size-change',
  'row-click',
])

// 响应式数据
const viewMode = ref('grid')

// 方法

const handleSizeChange = (size) => {
  emit('size-change', size)
}

const handlePageChange = (page) => {
  emit('page-change', page)
}

const handleRowClick = (row) => {
  emit('row-click', row)
}

const handleCommand = async (command) => {
  const [action, projectId] = command.split(':')

  switch (action) {
    case 'download':
      emit('download-project', projectId)
      break
    case 'duplicate':
      await handleDuplicateProject(projectId)
      break
    case 'archive':
      await handleArchiveProject(projectId)
      break
    case 'delete':
      await handleDeleteProject(projectId)
      break
  }
}

const handleDuplicateProject = async (projectId) => {
  try {
    const project = props.projects.find((p) => p.id === projectId)
    if (!project) return

    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要复制项目 "${project.title}" 吗？`,
      '确认复制',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'info',
      }
    )

    if (confirmed) {
      emit('duplicate-project', projectId)
      ElMessage.success('项目复制成功')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleArchiveProject = async (projectId) => {
  try {
    const project = props.projects.find((p) => p.id === projectId)
    if (!project) return

    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要${project.status === 'archived' ? '取消归档' : '归档'}项目 "${project.title}" 吗？`,
      '确认操作',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )

    if (confirmed) {
      emit('archive-project', projectId)
      ElMessage.success(project.status === 'archived' ? '项目已取消归档' : '项目已归档')
    }
  } catch (error) {
    // 用户取消操作
  }
}

const handleDeleteProject = async (projectId) => {
  try {
    const project = props.projects.find((p) => p.id === projectId)
    if (!project) return

    const { value: confirmed } = await ElMessageBox.confirm(
      `确定要删除项目 "${project.title}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'error',
        confirmButtonClass: 'el-button--danger',
      }
    )

    if (confirmed) {
      emit('delete-project', projectId)
      ElMessage.success('项目删除成功')
    }
  } catch (error) {
    // 用户取消操作
  }
}

// 工具方法
const getStatusType = (status) => {
  const typeMap = {
    draft: 'info',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
    archived: 'info',
  }
  return typeMap[status] || 'info'
}

const getStatusText = (status) => {
  const textMap = {
    draft: '草稿',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
    archived: '已归档',
  }
  return textMap[status] || status
}

const getFileStatusType = (status) => {
  const typeMap = {
    pending: 'info',
    uploading: 'warning',
    uploaded: 'success',
    processing: 'warning',
    completed: 'success',
    failed: 'danger',
  }
  return typeMap[status] || 'info'
}

const getFileStatusText = (status) => {
  const textMap = {
    pending: '等待',
    uploading: '上传中',
    uploaded: '已上传',
    processing: '处理中',
    completed: '已完成',
    failed: '失败',
  }
  return textMap[status] || status
}

const formatNumber = (num) => {
  if (!num) return '0'
  return num.toLocaleString()
}

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
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
  })
}

// 暴露给父组件的方法
defineExpose({
  getViewMode: () => viewMode.value,
})
</script>

<style scoped>
.project-list {
  width: 100%;
}

.view-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-lg);
  padding: 0 var(--space-sm);
}

.header-left {
  display: flex;
  align-items: center;
}

.header-right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.project-count {
  font-size: var(--text-base);
  color: var(--text-secondary);
  font-weight: 600;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-secondary);
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
}

.loading-container {
  padding: var(--space-xl);
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
}

.empty-state {
  padding: var(--space-2xl) var(--space-lg);
  text-align: center;
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.grid-view {
  width: 100%;
  overflow: visible; /* 确保内容不被裁剪 */
}

.grid-view .el-col {
  padding: var(--space-md);
}

/* Element Plus Row 组件可能需要的额外样式 */
:deep(.el-row) {
  width: 100%;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
}

/* 确保卡片容器有足够的空间 */
:deep(.el-col) {
  position: relative;
  overflow: visible;
}

/* 确保ProjectCard组件完全可见 */
.grid-view .project-card {
  position: relative;
  z-index: 1;
}

/* 表格样式优化 */
.list-view {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  overflow: hidden;
  box-shadow: var(--shadow-sm);
}

:deep(.el-table) {
  --el-table-border-color: var(--border-primary);
  --el-table-header-bg-color: var(--bg-secondary);
  --el-table-row-hover-bg-color: rgba(99, 102, 241, 0.05);
  --el-table-text-color: var(--text-primary);
  --el-table-header-text-color: var(--text-primary);
}

:deep(.el-table th) {
  font-weight: 700;
  font-size: var(--text-sm);
  background: var(--bg-secondary);
  border-bottom: 2px solid var(--border-primary);
}

:deep(.el-table td) {
  border-bottom: 1px solid var(--border-primary);
  padding: var(--space-md) var(--space-sm);
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: var(--bg-secondary);
}

.project-title {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

.title-text {
  flex: 1;
  min-width: 0;
  font-weight: 600;
  color: var(--text-primary);
}

/* 分页样式优化 */
.pagination-container {
  display: flex;
  justify-content: center;
  margin-top: var(--space-xl);
  padding: var(--space-xl) 0;
}

:deep(.el-pagination) {
  --el-pagination-button-bg-color: var(--bg-primary);
  --el-pagination-button-color: var(--text-primary);
  --el-pagination-hover-color: var(--primary-color);
  --el-pagination-bg-color: var(--bg-primary);
  --el-pagination-border-radius: var(--radius-lg);
  --el-pagination-font-size: var(--text-sm);
}

:deep(.el-pagination .el-pager li) {
  border-radius: var(--radius-lg);
  border: 1px solid var(--border-primary);
  margin: 0 2px;
}

:deep(.el-pagination .el-pager li:hover) {
  border-color: var(--primary-color);
}

:deep(.el-pagination .el-pager li.is-active) {
  background: var(--primary-color);
  color: white;
  border-color: var(--primary-color);
}

/* 按钮组样式 */
:deep(.el-button-group) {
  border-radius: var(--radius-lg);
  overflow: hidden;
}

:deep(.el-button-group .el-button) {
  border-radius: 0;
  border-right: none;
}

:deep(.el-button-group .el-button:first-child) {
  border-top-left-radius: var(--radius-lg);
  border-bottom-left-radius: var(--radius-lg);
}

:deep(.el-button-group .el-button:last-child) {
  border-top-right-radius: var(--radius-lg);
  border-bottom-right-radius: var(--radius-lg);
  border-right: 1px solid var(--border-primary);
}

:deep(.el-button-group .el-button--primary) {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border-color: var(--primary-color);
}

/* 视图切换按钮优化 */
:deep(.el-button-group .el-button) {
  transition: all var(--transition-base);
}

:deep(.el-button-group .el-button:hover) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

/* 标签样式优化 */
:deep(.el-tag) {
  border-radius: var(--radius-full);
  font-weight: 600;
  font-size: var(--text-xs);
  padding: var(--space-xs) var(--space-sm);
  border: 1px solid var(--border-primary);
}

:deep(.el-tag--info) {
  background: rgba(99, 102, 241, 0.1);
  color: var(--primary-color);
  border-color: rgba(99, 102, 241, 0.3);
}

:deep(.el-tag--success) {
  background: rgba(67, 197, 138, 0.1);
  color: var(--success-color);
  border-color: rgba(67, 197, 138, 0.3);
}

:deep(.el-tag--warning) {
  background: rgba(230, 162, 60, 0.1);
  color: var(--warning-color);
  border-color: rgba(230, 162, 60, 0.3);
}

:deep(.el-tag--danger) {
  background: rgba(245, 108, 108, 0.1);
  color: var(--danger-color);
  border-color: rgba(245, 108, 108, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .view-header {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-md);
    padding: 0;
  }

  .header-right {
    width: 100%;
    justify-content: flex-end;
  }

  .project-count {
    order: -1;
  }

  .grid-view {
    width: 100%;
    overflow: visible;
  }

  .grid-view .el-col {
    padding: var(--space-sm);
  }

  .loading-container,
  .empty-state {
    padding: var(--space-lg) var(--space-md);
  }

  :deep(.el-table) {
    font-size: var(--text-sm);
  }

  :deep(.el-table th),
  :deep(.el-table td) {
    padding: var(--space-sm);
  }

  .pagination-container {
    padding: var(--space-lg) 0;
    margin-top: var(--space-lg);
  }

  :deep(.el-button-group .el-button) {
    padding: var(--space-xs) var(--space-sm);
    font-size: var(--text-xs);
  }
}

@media (max-width: 480px) {
  .view-header {
    gap: var(--space-sm);
  }

  .project-count {
    font-size: var(--text-sm);
    padding: var(--space-xs) var(--space-sm);
  }

  .loading-container,
  .empty-state {
    padding: var(--space-md);
  }

  :deep(.el-table) {
    font-size: var(--text-xs);
  }

  :deep(.el-table th),
  :deep(.el-table td) {
    padding: var(--space-xs);
  }

  .project-title {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-xs);
  }
}

/* 深色主题适配 */
@media (prefers-color-scheme: dark) {
  :deep(.el-table) {
    --el-table-border-color: var(--border-primary);
    --el-table-header-bg-color: var(--bg-dark);
    --el-table-row-hover-bg-color: rgba(99, 102, 241, 0.1);
  }

  :deep(.el-descriptions) {
    --el-descriptions-table-border: 1px solid var(--border-primary);
    --el-descriptions-item-bordered-background: var(--bg-dark);
  }
}
</style>