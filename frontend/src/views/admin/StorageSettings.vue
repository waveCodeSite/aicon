<template>
  <div class="storage-settings">
    <div class="page-header">
      <h2>存储配置</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        添加存储源
      </el-button>
    </div>

    <!-- 存储源列表 -->
    <el-card v-loading="loading">
      <el-table :data="sources" stripe>
        <el-table-column prop="name" label="名称" width="150" />
        <el-table-column prop="provider" label="提供商" width="100">
          <template #default="{ row }">
            <el-tag size="small">{{ providerLabels[row.provider] || row.provider }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="endpoint" label="端点" min-width="200" />
        <el-table-column prop="bucket" label="存储桶" width="120" />
        <el-table-column label="状态" width="80">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">
              {{ row.is_active ? '已启用' : '未启用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="280" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="browseFiles(row)">浏览</el-button>
            <el-button size="small" @click="editSource(row)">编辑</el-button>
            <el-button size="small" type="success" v-if="!row.is_active" @click="activateSource(row)">启用</el-button>
            <el-button size="small" type="warning" v-if="row.is_active" @click="deactivateSource(row)">禁用</el-button>
            <el-button size="small" type="danger" v-if="!row.is_active" @click="deleteSource(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑存储源' : '添加存储源'" width="550px">
      <el-form :model="form" :rules="rules" ref="formRef" label-width="100px">
        <el-form-item label="名称" prop="name">
          <el-input v-model="form.name" placeholder="存储源名称" />
        </el-form-item>
        <el-form-item label="提供商" prop="provider">
          <el-select v-model="form.provider" style="width: 100%">
            <el-option label="MinIO" value="minio" />
            <el-option label="AWS S3" value="aws" />
            <el-option label="阿里云 OSS" value="aliyun" />
            <el-option label="腾讯云 COS" value="tencent" />
            <el-option label="华为云 OBS" value="huawei" />
            <el-option label="Cloudflare R2" value="cloudflare" />
          </el-select>
        </el-form-item>
        <el-form-item label="端点" prop="endpoint">
          <el-input v-model="form.endpoint" placeholder="例如: localhost:9000">
            <template #prepend>
              <el-select v-model="form.secure" style="width: 100px">
                <el-option label="http://" :value="false" />
                <el-option label="https://" :value="true" />
              </el-select>
            </template>
          </el-input>
        </el-form-item>
        <el-form-item label="Access Key" prop="access_key">
          <el-input v-model="form.access_key" />
        </el-form-item>
        <el-form-item label="Secret Key" prop="secret_key">
          <el-input v-model="form.secret_key" type="password" show-password :placeholder="isEdit ? '留空则不修改' : ''" />
        </el-form-item>
        <el-form-item label="存储桶" prop="bucket">
          <el-input v-model="form.bucket" />
        </el-form-item>
        <el-form-item label="区域" prop="region">
          <el-input v-model="form.region" placeholder="us-east-1" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="testConnection" :loading="testing">测试连接</el-button>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">保存</el-button>
      </template>
    </el-dialog>

    <!-- 文件浏览对话框 -->
    <el-dialog v-model="filesDialogVisible" :title="`文件浏览 - ${currentSource?.name}`" width="800px">
      <div class="files-toolbar">
        <el-input v-model="filePrefix" placeholder="路径前缀" style="width: 300px" @keyup.enter="loadFiles">
          <template #append>
            <el-button @click="loadFiles">搜索</el-button>
          </template>
        </el-input>
      </div>
      <el-table :data="files" v-loading="filesLoading" max-height="400">
        <el-table-column prop="key" label="文件路径" min-width="300" />
        <el-table-column label="大小" width="100">
          <template #default="{ row }">{{ formatSize(row.size) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="deleteFile(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import adminService from '@/services/admin'

const loading = ref(false)
const submitting = ref(false)
const testing = ref(false)
const dialogVisible = ref(false)
const isEdit = ref(false)
const editingId = ref(null)
const formRef = ref(null)
const sources = ref([])

const providerLabels = {
  minio: 'MinIO',
  aws: 'AWS S3',
  aliyun: '阿里云',
  tencent: '腾讯云',
  huawei: '华为云',
  cloudflare: 'R2'
}

const form = reactive({
  name: '',
  provider: 'minio',
  endpoint: '',
  access_key: '',
  secret_key: '',
  bucket: '',
  region: 'us-east-1',
  secure: false
})

const rules = {
  name: [{ required: true, message: '请输入名称', trigger: 'blur' }],
  provider: [{ required: true, message: '请选择提供商', trigger: 'change' }],
  endpoint: [{ required: true, message: '请输入端点', trigger: 'blur' }],
  access_key: [{ required: true, message: '请输入 Access Key', trigger: 'blur' }],
  bucket: [{ required: true, message: '请输入存储桶', trigger: 'blur' }]
}

// 文件浏览
const filesDialogVisible = ref(false)
const filesLoading = ref(false)
const currentSource = ref(null)
const filePrefix = ref('')
const files = ref([])

const loadSources = async () => {
  loading.value = true
  try {
    sources.value = await adminService.getStorageSources()
  } catch {
    ElMessage.error('加载存储源失败')
  } finally {
    loading.value = false
  }
}

const showCreateDialog = () => {
  isEdit.value = false
  editingId.value = null
  Object.assign(form, {
    name: '', provider: 'minio', endpoint: '', access_key: '',
    secret_key: '', bucket: '', region: 'us-east-1', secure: false
  })
  dialogVisible.value = true
}

const editSource = (source) => {
  isEdit.value = true
  editingId.value = source.id
  Object.assign(form, {
    name: source.name,
    provider: source.provider,
    endpoint: source.endpoint,
    access_key: source.access_key,
    secret_key: '',
    bucket: source.bucket,
    region: source.region,
    secure: source.secure
  })
  dialogVisible.value = true
}

const testConnection = async () => {
  if (!form.secret_key && !isEdit.value) {
    ElMessage.warning('请输入 Secret Key')
    return
  }
  testing.value = true
  try {
    const result = await adminService.testStorageConnection(form)
    if (result.success) {
      ElMessage.success('连接成功')
    } else {
      ElMessage.error(`连接失败: ${result.message}`)
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '测试失败')
  } finally {
    testing.value = false
  }
}

const submitForm = async () => {
  await formRef.value?.validate()
  if (!form.secret_key && !isEdit.value) {
    ElMessage.warning('请输入 Secret Key')
    return
  }
  submitting.value = true
  try {
    if (isEdit.value) {
      await adminService.updateStorageSource(editingId.value, form)
      ElMessage.success('更新成功')
    } else {
      await adminService.createStorageSource(form)
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadSources()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const activateSource = async (source) => {
  try {
    await adminService.activateStorageSource(source.id)
    ElMessage.success('已启用')
    loadSources()
  } catch (e) {
    ElMessage.error(e.response?.data?.detail || '启用失败')
  }
}

const deactivateSource = async (source) => {
  try {
    await ElMessageBox.confirm('禁用后将使用环境变量中的默认存储配置，确定禁用？', '确认禁用', { type: 'warning' })
    await adminService.deactivateStorageSource(source.id)
    ElMessage.success('已禁用')
    loadSources()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '禁用失败')
  }
}

const deleteSource = async (source) => {
  try {
    await ElMessageBox.confirm(`确定删除存储源 "${source.name}"？`, '确认删除', { type: 'warning' })
    await adminService.deleteStorageSource(source.id)
    ElMessage.success('已删除')
    loadSources()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const browseFiles = (source) => {
  currentSource.value = source
  filePrefix.value = ''
  files.value = []
  filesDialogVisible.value = true
  loadFiles()
}

const loadFiles = async () => {
  if (!currentSource.value) return
  filesLoading.value = true
  try {
    files.value = await adminService.listStorageFiles(currentSource.value.id, filePrefix.value)
  } catch {
    ElMessage.error('加载文件失败')
  } finally {
    filesLoading.value = false
  }
}

const deleteFile = async (file) => {
  try {
    await ElMessageBox.confirm(`确定删除文件 "${file.key}"？`, '确认删除', { type: 'warning' })
    await adminService.deleteStorageFile(currentSource.value.id, file.key)
    ElMessage.success('已删除')
    loadFiles()
  } catch (e) {
    if (e !== 'cancel') ElMessage.error(e.response?.data?.detail || '删除失败')
  }
}

const formatSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  if (bytes < 1024 * 1024 * 1024) return (bytes / 1024 / 1024).toFixed(1) + ' MB'
  return (bytes / 1024 / 1024 / 1024).toFixed(1) + ' GB'
}

onMounted(() => {
  loadSources()
})
</script>

<style scoped>
.storage-settings {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.page-header h2 {
  margin: 0;
}

.files-toolbar {
  margin-bottom: 16px;
}
</style>
