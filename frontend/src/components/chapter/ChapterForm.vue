<template>
  <div class="chapter-form">
    <el-form
      ref="formRef"
      :model="formData"
      :rules="formRules"
      label-width="100px"
      label-position="top"
      @submit.prevent="handleSubmit"
    >
      <el-form-item label="章节标题" prop="title">
        <el-input
          v-model="formData.title"
          placeholder="请输入章节标题"
          maxlength="500"
          show-word-limit
          clearable
        />
      </el-form-item>

      <el-form-item label="章节序号" prop="chapter_number">
        <el-input-number
          v-model="formData.chapter_number"
          :min="1"
          placeholder="请输入章节序号"
          style="width: 200px"
        />
      </el-form-item>

      <el-form-item label="章节内容" prop="content">
        <el-input
          v-model="formData.content"
          type="textarea"
          :rows="10"
          placeholder="请输入章节内容"
          maxlength="10000"
          show-word-limit
          resize="vertical"
        />
      </el-form-item>

      <el-form-item>
        <div class="content-preview">
          <div class="preview-header">
            <span>内容预览</span>
            <span class="word-count">字数: {{ formData.content.length }}</span>
          </div>
          <div class="preview-content">
            <pre v-if="formData.content">{{ formData.content }}</pre>
            <div v-else class="empty-preview">暂无内容</div>
          </div>
        </div>
      </el-form-item>
    </el-form>

    <div class="form-actions">
      <el-button @click="handleCancel">取消</el-button>
      <el-button
        type="primary"
        @click="handleSubmit"
        :loading="submitting"
        :disabled="!isFormValid"
      >
        {{ editingChapter ? '更新章节' : '创建章节' }}
      </el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'

// Props
const props = defineProps({
  chapter: {
    type: Object,
    default: null
  },
  projectId: {
    type: String,
    required: true
  }
})

// Emits
const emit = defineEmits(['submit', 'cancel'])

// 响应式数据
const formRef = ref()
const submitting = ref(false)

const formData = reactive({
  title: '',
  chapter_number: 1,
  content: ''
})

// 表单验证规则
const formRules = {
  title: [
    { required: true, message: '请输入章节标题', trigger: 'blur' },
    { min: 1, max: 500, message: '标题长度应在1-500字符之间', trigger: 'blur' }
  ],
  chapter_number: [
    { required: true, message: '请输入章节序号', trigger: 'blur' },
    { type: 'number', min: 1, message: '章节序号必须大于0', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入章节内容', trigger: 'blur' },
    { min: 10, message: '章节内容至少需要10个字符', trigger: 'blur' },
    { max: 10000, message: '章节内容不能超过10000个字符', trigger: 'blur' }
  ]
}

// 计算属性
const editingChapter = computed(() => !!props.chapter)

const isFormValid = computed(() => {
  return formData.title.trim().length > 0 &&
         formData.chapter_number > 0 &&
         formData.content.trim().length >= 10
})

// 方法
const initFormData = () => {
  if (props.chapter) {
    formData.title = props.chapter.title || ''
    formData.chapter_number = props.chapter.chapter_number || 1
    formData.content = props.chapter.content || ''
  } else {
    // 新建章节时，设置默认值
    formData.title = ''
    formData.chapter_number = 1
    formData.content = ''
  }
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    const valid = await formRef.value.validate()
    if (!valid) {
      ElMessage.warning('请完善表单信息')
      return
    }

    submitting.value = true

    const submitData = {
      title: formData.title.trim(),
      chapter_number: formData.chapter_number,
      content: formData.content.trim()
    }

    emit('submit', submitData)
  } catch (error) {
    ElMessage.error('表单验证失败')
    console.error('表单验证失败:', error)
  } finally {
    submitting.value = false
  }
}

const handleCancel = () => {
  emit('cancel')
}

// 监听章节变化，初始化表单数据
watch(() => props.chapter, () => {
  initFormData()
}, { immediate: true })

// 初始化
initFormData()
</script>

<style scoped>
.chapter-form {
  display: flex;
  flex-direction: column;
  gap: var(--space-lg);
}

:deep(.el-form-item__label) {
  font-weight: 600;
  color: var(--text-primary);
}

.content-preview {
  width: 100%;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-md);
  background: var(--bg-secondary);
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  background: var(--bg-primary);
  border-bottom: 1px solid var(--border-primary);
  font-size: var(--text-sm);
  font-weight: 500;
  color: var(--text-primary);
}

.word-count {
  color: var(--text-secondary);
  font-size: var(--text-xs);
}

.preview-content {
  padding: var(--space-md);
  min-height: 100px;
  max-height: 200px;
  overflow-y: auto;
}

.preview-content pre {
  margin: 0;
  font-family: inherit;
  font-size: var(--text-sm);
  line-height: 1.6;
  color: var(--text-secondary);
  white-space: pre-wrap;
  word-wrap: break-word;
}

.empty-preview {
  color: var(--text-placeholder);
  text-align: center;
  padding: var(--space-lg) 0;
  font-style: italic;
}

.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-md);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-primary);
}

:deep(.el-button) {
  padding: var(--space-md) var(--space-lg);
  border-radius: var(--radius-lg);
  font-weight: 600;
  min-width: 100px;
}

:deep(.el-button--primary) {
  background: linear-gradient(135deg, var(--primary-color), var(--primary-hover));
  border: none;
}

:deep(.el-button--primary:hover:not(:disabled)) {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
}

:deep(.el-input-number) {
  width: 100%;
}

:deep(.el-textarea) {
  font-family: inherit;
}

:deep(.el-textarea__inner) {
  font-family: inherit;
  line-height: 1.6;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .form-actions {
    flex-direction: column;
  }

  :deep(.el-button) {
    width: 100%;
  }
}
</style>