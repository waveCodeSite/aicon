<template>
  <div class="user-management">
    <div class="page-header">
      <h2>用户管理</h2>
      <el-button type="primary" @click="showCreateDialog">
        <el-icon><Plus /></el-icon>
        创建用户
      </el-button>
    </div>

    <!-- 系统设置 -->
    <el-card class="settings-card">
      <div class="setting-item">
        <span>允许用户注册</span>
        <el-switch
          v-model="allowRegistration"
          :loading="settingsLoading"
          @change="updateRegistrationSetting"
        />
      </div>
    </el-card>

    <!-- 搜索和筛选 -->
    <el-card class="filter-card">
      <el-form :inline="true" :model="filters">
        <el-form-item label="搜索">
          <el-input
            v-model="filters.search"
            placeholder="用户名/邮箱"
            clearable
            @keyup.enter="loadUsers"
          />
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filters.is_active" placeholder="全部" style="width: 100px" clearable>
            <el-option label="激活" :value="true" />
            <el-option label="禁用" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="filters.is_admin" placeholder="全部" style="width: 100px" clearable>
            <el-option label="管理员" :value="true" />
            <el-option label="普通用户" :value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadUsers">搜索</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <!-- 用户列表 -->
    <el-card>
      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="150" />
        <el-table-column prop="email" label="邮箱" width="200" />
        <el-table-column prop="display_name" label="显示名称" width="150" />
        <el-table-column label="角色" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_admin ? 'danger' : 'info'" size="small">
              {{ row.is_admin ? '管理员' : '用户' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '激活' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="180">
          <template #default="{ row }">
            {{ row.last_login ? formatDate(row.last_login) : '-' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="200" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="editUser(row)">编辑</el-button>
            <el-button
              size="small"
              :type="row.is_active ? 'warning' : 'success'"
              @click="toggleActive(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
            <el-button size="small" type="danger" @click="deleteUser(row)">
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <!-- 分页 -->
      <el-pagination
        v-model:current-page="pagination.page"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next"
        @size-change="loadUsers"
        @current-change="loadUsers"
        class="pagination"
      />
    </el-card>

    <!-- 创建/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑用户' : '创建用户'"
      width="500px"
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="80px">
        <el-form-item label="用户名" prop="username" v-if="!isEdit">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="邮箱" prop="email" v-if="!isEdit">
          <el-input v-model="form.email" />
        </el-form-item>
        <el-form-item label="密码" prop="password" v-if="!isEdit">
          <el-input v-model="form.password" type="password" show-password />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" />
        </el-form-item>
        <el-form-item label="管理员">
          <el-switch v-model="form.is_admin" />
        </el-form-item>
        <el-form-item label="激活" v-if="isEdit">
          <el-switch v-model="form.is_active" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm" :loading="submitting">
          确定
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import adminService from '@/services/admin'
import { useSystemStore } from '@/stores/system'
import { storeToRefs } from 'pinia'

const systemStore = useSystemStore()
const { allowRegistration } = storeToRefs(systemStore)
const settingsLoading = ref(false)

const loading = ref(false)
const submitting = ref(false)
const users = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const formRef = ref(null)
const editingUserId = ref(null)

const filters = reactive({
  search: '',
  is_active: null,
  is_admin: null
})

const pagination = reactive({
  page: 1,
  pageSize: 20,
  total: 0
})

const form = reactive({
  username: '',
  email: '',
  password: '',
  display_name: '',
  is_admin: false,
  is_active: true
})

const rules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '长度在 3 到 50 个字符', trigger: 'blur' }
  ],
  email: [
    { required: true, message: '请输入邮箱', trigger: 'blur' },
    { type: 'email', message: '请输入正确的邮箱格式', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' }
  ]
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleString('zh-CN')
}

const loadUsers = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.page,
      page_size: pagination.pageSize,
      ...filters
    }
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === null || params[key] === '') {
        delete params[key]
      }
    })
    const data = await adminService.getUsers(params)
    console.log(data)
    users.value = data.users
    pagination.total = data.total
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const resetFilters = () => {
  filters.search = ''
  filters.is_active = null
  filters.is_admin = null
  pagination.page = 1
  loadUsers()
}

const showCreateDialog = () => {
  isEdit.value = false
  editingUserId.value = null
  Object.assign(form, {
    username: '',
    email: '',
    password: '',
    display_name: '',
    is_admin: false,
    is_active: true
  })
  dialogVisible.value = true
}

const editUser = (user) => {
  isEdit.value = true
  editingUserId.value = user.id
  Object.assign(form, {
    display_name: user.display_name || '',
    is_admin: user.is_admin,
    is_active: user.is_active
  })
  dialogVisible.value = true
}

const submitForm = async () => {
  if (!isEdit.value) {
    await formRef.value?.validate()
  }

  submitting.value = true
  try {
    if (isEdit.value) {
      await adminService.updateUser(editingUserId.value, {
        is_admin: form.is_admin,
        is_active: form.is_active
      })
      ElMessage.success('更新成功')
    } else {
      await adminService.createUser({
        username: form.username,
        email: form.email,
        password: form.password,
        display_name: form.display_name,
        is_admin: form.is_admin
      })
      ElMessage.success('创建成功')
    }
    dialogVisible.value = false
    loadUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

const toggleActive = async (user) => {
  try {
    await adminService.toggleUserActive(user.id)
    ElMessage.success(user.is_active ? '已禁用' : '已启用')
    loadUsers()
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复。`,
      '删除确认',
      { type: 'warning' }
    )
    await adminService.deleteUser(user.id)
    ElMessage.success('删除成功')
    loadUsers()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}

const updateRegistrationSetting = async (value) => {
  settingsLoading.value = true
  try {
    await systemStore.updateSettings({ allow_registration: value })
    ElMessage.success(value ? '已开启注册' : '已关闭注册')
  } catch {
    ElMessage.error('更新设置失败')
    allowRegistration.value = !value
  } finally {
    settingsLoading.value = false
  }
}

onMounted(() => {
  loadUsers()
  systemStore.fetchSettings()
})
</script>

<style scoped>
.user-management {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h2 {
  margin: 0;
}

.settings-card {
  margin-bottom: 0;
}

.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.filter-card {
  margin-bottom: 0;
}

.pagination {
  margin-top: 20px;
  justify-content: flex-end;
}
</style>
