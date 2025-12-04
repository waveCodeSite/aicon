<template>
  <div class="bgm-management">
    <!-- 统计卡片 -->
    <el-row :gutter="20" class="stats-row">
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-card">
            <el-icon class="stat-icon" color="#409EFF"><Headset /></el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_count }}</div>
              <div class="stat-label">总BGM数量</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-card">
            <el-icon class="stat-icon" color="#67C23A"><FolderOpened /></el-icon>
            <div class="stat-content">
              <div class="stat-value">{{ stats.total_size_mb }} MB</div>
              <div class="stat-label">总存储空间</div>
            </div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card shadow="hover">
          <div class="stat-card">
            <el-icon class="stat-icon" color="#E6A23C"><Upload /></el-icon>
            <div class="stat-content">
              <el-button type="primary" @click="showUploadDialog = true">
                <el-icon><Upload /></el-icon> 上传BGM
              </el-button>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- BGM列表 -->
    <el-card class="table-card">
      <template #header>
        <div class="card-header">
          <span>BGM列表</span>
          <el-button type="primary" @click="refreshList">
            <el-icon><Refresh /></el-icon> 刷新
          </el-button>
        </div>
      </template>

      <el-table
        v-loading="loading"
        :data="bgms"
        stripe
        style="width: 100%"
      >
        <el-table-column prop="name" label="名称" min-width="200" />
        <el-table-column prop="file_name" label="文件名" min-width="200" />
        <el-table-column label="时长" width="100">
          <template #default="{ row }">
            {{ formatDuration(row.duration) }}
          </template>
        </el-table-column>
        <el-table-column label="文件大小" width="120">
          <template #default="{ row }">
            {{ formatFileSize(row.file_size) }}
          </template>
        </el-table-column>
        <el-table-column prop="created_at" label="上传时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button-group>
              <el-button size="small" @click="previewBGM(row)">
                <el-icon><VideoPlay /></el-icon> 试听
              </el-button>
              <el-button size="small" type="danger" @click="handleDelete(row)">
                <el-icon><Delete /></el-icon> 删除
              </el-button>
            </el-button-group>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @size-change="changePageSize"
          @current-change="changePage"
        />
      </div>
    </el-card>

    <!-- 上传对话框 -->
    <UploadBGMDialog
      v-model="showUploadDialog"
      @success="handleUploadSuccess"
    />

    <!-- 试听对话框 -->
    <el-dialog
      v-model="showPreviewDialog"
      title="试听BGM"
      width="500px"
    >
      <div v-if="currentBGM" class="preview-container">
        <div class="preview-info">
          <p><strong>名称：</strong>{{ currentBGM.name }}</p>
          <p><strong>时长：</strong>{{ formatDuration(currentBGM.duration) }}</p>
        </div>
        <audio
          v-if="currentBGM.file_url"
          controls
          class="audio-player"
          :src="currentBGM.file_url"
        >
          您的浏览器不支持音频播放
        </audio>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'
import { Headset, FolderOpened, Upload, Refresh, VideoPlay, Delete } from '@element-plus/icons-vue'
import { useBGM } from '@/composables/useBGM'
import { formatDate } from '@/utils/dateUtils'
import UploadBGMDialog from '@/components/bgm/UploadBGMDialog.vue'

const {
  bgms,
  loading,
  stats,
  pagination,
  fetchBGMs,
  deleteBGM,
  refreshStats,
  changePage,
  changePageSize
} = useBGM()

const showUploadDialog = ref(false)
const showPreviewDialog = ref(false)
const currentBGM = ref(null)

onMounted(async () => {
  await fetchBGMs()
  await refreshStats()
})

const refreshList = async () => {
  await fetchBGMs()
  await refreshStats()
}

const formatDuration = (seconds) => {
  if (!seconds) return '-'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${m}:${s.toString().padStart(2, '0')}`
}

const formatFileSize = (bytes) => {
  if (!bytes) return '-'
  const mb = bytes / (1024 * 1024)
  return mb < 1 ? `${(bytes / 1024).toFixed(2)} KB` : `${mb.toFixed(2)} MB`
}

const previewBGM = (bgm) => {
  currentBGM.value = bgm
  showPreviewDialog.value = true
}

const handleDelete = async (bgm) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除BGM "${bgm.name}" 吗？此操作不可恢复。`,
      '确认删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
    
    await deleteBGM(bgm.id)
  } catch (error) {
    if (error !== 'cancel') {
      console.error('删除失败:', error)
    }
  }
}

const handleUploadSuccess = () => {
  showUploadDialog.value = false
  refreshList()
}
</script>

<style scoped>
.bgm-management {
  padding: 20px;
}

.stats-row {
  margin-bottom: 20px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  font-size: 48px;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: var(--text-primary);
}

.stat-label {
  font-size: 14px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.table-card {
  margin-top: 20px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.pagination-container {
  margin-top: 20px;
  display: flex;
  justify-content: flex-end;
}

.preview-container {
  padding: 20px 0;
}

.preview-info {
  margin-bottom: 20px;
}

.preview-info p {
  margin: 8px 0;
  font-size: 14px;
}

.audio-player {
  width: 100%;
  margin-top: 10px;
}
</style>
