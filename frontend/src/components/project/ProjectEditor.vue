<template>
  <div class="project-editor">
    <!-- 项目信息表单 -->
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-position="top"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="项目标题" prop="title">
        <el-input
          v-model="formData.title"
          placeholder="请输入项目标题"
          maxlength="200"
          show-word-limit
          clearable
          :disabled="loading"
        />
      </el-form-item>

      <el-form-item label="项目描述" prop="description">
        <el-input
          v-model="formData.description"
          type="textarea"
          :rows="4"
          placeholder="请输入项目描述（可选）"
          maxlength="1000"
          show-word-limit
          :disabled="loading"
        />
      </el-form-item>

      <div class="form-actions">
        <el-button @click="handleCancel" :disabled="loading">取消</el-button>
        <el-button
          type="primary"
          native-type="submit"
          :loading="loading"
        >
          保存修改
        </el-button>
      </div>
    </el-form>
  </div>
</template>

<script setup>
import { ref, reactive, watch, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { projectsService } from '@/services/projects'

// Props定义
const props = defineProps({
  // 项目数据
  project: {
    type: Object,
    required: true
  },
  // 表单提交loading状态
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits定义
const emit = defineEmits([
  'submit',
  'cancel',
  'error'
])

// 响应式数据
const formRef = ref()

// 表单数据
const formData = reactive({
  title: '',
  description: ''
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入项目标题', trigger: 'blur' },
    { min: 1, max: 200, message: '标题长度应在1-200个字符之间', trigger: 'blur' }
  ],
  description: [
    { max: 1000, message: '描述长度不能超过1000个字符', trigger: 'blur' }
  ]
}

// 监听project变化，更新表单数据
watch(() => props.project, (newProject) => {
  if (newProject) {
    formData.title = newProject.title || ''
    formData.description = newProject.description || ''
  }
}, { immediate: true })

// 初始化表单数据
onMounted(() => {
  if (props.project) {
    formData.title = props.project.title || ''
    formData.description = props.project.description || ''
  }
})

// 方法
const handleSubmit = async () => {
  try {
    // 验证表单
    const valid = await formRef.value.validate()
    if (!valid) return

    // 准备更新数据 - 只包含标题和描述
    const updateData = {
      title: formData.title.trim(),
      description: formData.description.trim()
    }

    // 检查是否有实际变更
    if (updateData.title === props.project.title &&
        updateData.description === props.project.description) {
      ElMessage.info('没有检测到任何变更')
      return
    }

    // 调用项目API更新项目
    const result = await projectsService.updateProject(props.project.id, updateData)

    ElMessage.success('项目更新成功')
    emit('submit', result)

  } catch (error) {
    console.error('项目更新失败:', error)
    ElMessage.error(error.message || '项目更新失败')
    emit('error', error)
  }
}

const handleCancel = () => {
  // 恢复原始数据
  if (props.project) {
    formData.title = props.project.title || ''
    formData.description = props.project.description || ''
  }

  // 清除验证结果
  if (formRef.value) {
    formRef.value.clearValidate()
  }

  emit('cancel')
}

const resetForm = () => {
  // 重置表单数据为项目原始数据
  if (props.project) {
    formData.title = props.project.title || ''
    formData.description = props.project.description || ''
  }

  if (formRef.value) {
    formRef.value.clearValidate()
  }
}

// 暴露给父组件的方法
defineExpose({
  resetForm,
  validate: () => formRef.value?.validate()
})
</script>

<style scoped>
.project-editor {
  width: 100%;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  margin-top: var(--space-lg);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-primary);
}

/* 表单项样式优化 */
:deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary);
}

:deep(.el-input__wrapper) {
  transition: all var(--transition-base);
}

:deep(.el-input__wrapper:hover) {
  border-color: var(--primary-color);
}

:deep(.el-input__wrapper.is-focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

:deep(.el-textarea__inner) {
  transition: all var(--transition-base);
}

:deep(.el-textarea__inner:hover) {
  border-color: var(--primary-color);
}

:deep(.el-textarea__inner:focus) {
  border-color: var(--primary-color);
  box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.1);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
    gap: var(--space-sm);
  }

  .form-actions :deep(.el-button) {
    width: 100%;
  }
}
</style>