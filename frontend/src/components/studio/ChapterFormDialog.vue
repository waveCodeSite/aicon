<template>
  <el-dialog
    v-model="visible"
    :title="isEdit ? '编辑章节' : '创建章节'"
    width="600px"
    @close="handleClose"
  >
    <el-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      label-width="100px"
    >
      <el-form-item label="章节标题" prop="title">
        <el-input
          v-model="formData.title"
          placeholder="请输入章节标题"
          maxlength="200"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="章节序号" prop="chapter_number">
        <el-input-number
          v-model="formData.chapter_number"
          :min="1"
          :max="9999"
          placeholder="章节序号"
        />
      </el-form-item>

      <el-form-item label="章节内容" prop="content">
        <el-input
          v-model="formData.content"
          type="textarea"
          :rows="10"
          placeholder="请输入章节内容"
          maxlength="50000"
          show-word-limit
        />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" @click="handleSubmit" :loading="loading">
        {{ isEdit ? '保存' : '创建' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  modelValue: {
    type: Boolean,
    default: false
  },
  chapter: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'submit'])

const visible = ref(false)
const formRef = ref()
const loading = ref(false)

const formData = ref({
  title: '',
  chapter_number: 1,
  content: ''
})

const rules = {
  title: [
    { required: true, message: '请输入章节标题', trigger: 'blur' }
  ],
  chapter_number: [
    { required: true, message: '请输入章节序号', trigger: 'blur' }
  ],
  content: [
    { required: true, message: '请输入章节内容', trigger: 'blur' }
  ]
}

const isEdit = ref(false)

watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    if (props.chapter) {
      // 编辑模式
      isEdit.value = true
      formData.value = {
        title: props.chapter.title || '',
        chapter_number: props.chapter.chapter_number || 1,
        content: props.chapter.content || ''
      }
    } else {
      // 创建模式
      isEdit.value = false
      formData.value = {
        title: '',
        chapter_number: 1,
        content: ''
      }
    }
  }
})

watch(visible, (val) => {
  emit('update:modelValue', val)
})

const handleClose = () => {
  visible.value = false
  formRef.value?.resetFields()
}

const handleSubmit = async () => {
  const valid = await formRef.value?.validate()
  if (!valid) return

  loading.value = true
  try {
    emit('submit', {
      ...formData.value,
      id: props.chapter?.id
    })
    handleClose()
  } finally {
    loading.value = false
  }
}
</script>
