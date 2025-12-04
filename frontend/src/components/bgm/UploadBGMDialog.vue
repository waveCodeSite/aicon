<template>
  <el-dialog
    title="上传BGM"
    :model-value="modelValue"
    @update:model-value="$emit('update:modelValue', $event)"
    width="500px"
    destroy-on-close
  >
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="80px"
    >
      <el-form-item label="BGM名称" prop="name">
        <el-input
          v-model="form.name"
          placeholder="请输入BGM名称"
          maxlength="100"
          show-word-limit
        />
      </el-form-item>

      <el-form-item label="选择文件" prop="file">
        <el-upload
          ref="uploadRef"
          :auto-upload="false"
          :limit="1"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          :file-list="fileList"
          accept=".mp3,.wav,.m4a,.aac,.ogg"
          drag
        >
          <el-icon class="el-icon--upload"><upload-filled /></el-icon>
          <div class="el-upload__text">
            拖拽文件到此处或 <em>点击上传</em>
          </div>
          <template #tip>
            <div class="el-upload__tip">
              支持 MP3、WAV、M4A、AAC、OGG 格式，文件大小不超过 50MB
            </div>
          </template>
        </el-upload>
      </el-form-item>

      <el-form-item v-if="uploadProgress > 0 && uploadProgress < 100">
        <el-progress :percentage="uploadProgress" />
      </el-form-item>
    </el-form>

    <template #footer>
      <el-button @click="handleCancel">取消</el-button>
      <el-button
        type="primary"
        :loading="uploading"
        :disabled="!form.file"
        @click="handleSubmit"
      >
        {{ uploading ? '上传中...' : '确定上传' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { useBGM } from '@/composables/useBGM'

const props = defineProps({
  modelValue: Boolean
})

const emit = defineEmits(['update:modelValue', 'success'])

const { uploadBGM } = useBGM()

const formRef = ref(null)
const uploadRef = ref(null)
const uploading = ref(false)
const uploadProgress = ref(0)
const fileList = ref([])

const form = reactive({
  name: '',
  file: null
})

const rules = {
  name: [
    { required: true, message: '请输入BGM名称', trigger: 'blur' },
    { min: 1, max: 100, message: '名称长度在 1 到 100 个字符', trigger: 'blur' }
  ],
  file: [
    { required: true, message: '请选择文件', trigger: 'change' }
  ]
}

watch(() => props.modelValue, (val) => {
  if (!val) {
    resetForm()
  }
})

const handleFileChange = (file) => {
  // 验证文件大小
  const maxSize = 50 * 1024 * 1024 // 50MB
  if (file.size > maxSize) {
    ElMessage.error('文件大小不能超过 50MB')
    uploadRef.value.clearFiles()
    return
  }

  // 验证文件类型
  const allowedTypes = ['.mp3', '.wav', '.m4a', '.aac', '.ogg']
  const fileName = file.name.toLowerCase()
  const isAllowed = allowedTypes.some(ext => fileName.endsWith(ext))
  
  if (!isAllowed) {
    ElMessage.error('不支持的文件格式')
    uploadRef.value.clearFiles()
    return
  }

  form.file = file.raw
  fileList.value = [file]
  
  // 自动填充名称（如果为空）
  if (!form.name) {
    form.name = file.name.replace(/\.[^/.]+$/, '')
  }
}

const handleFileRemove = () => {
  form.file = null
  fileList.value = []
}

const handleSubmit = async () => {
  if (!formRef.value) return

  try {
    await formRef.value.validate()
    
    uploading.value = true
    uploadProgress.value = 0

    // 模拟上传进度
    const progressInterval = setInterval(() => {
      if (uploadProgress.value < 90) {
        uploadProgress.value += 10
      }
    }, 200)

    await uploadBGM(form.file, form.name)
    
    clearInterval(progressInterval)
    uploadProgress.value = 100
    
    emit('success')
    emit('update:modelValue', false)
    
  } catch (error) {
    console.error('上传失败:', error)
  } finally {
    uploading.value = false
    uploadProgress.value = 0
  }
}

const handleCancel = () => {
  emit('update:modelValue', false)
}

const resetForm = () => {
  if (formRef.value) {
    formRef.value.resetFields()
  }
  if (uploadRef.value) {
    uploadRef.value.clearFiles()
  }
  form.file = null
  fileList.value = []
  uploadProgress.value = 0
}
</script>

<style scoped>
.el-upload__tip {
  font-size: 12px;
  color: var(--text-secondary);
  margin-top: 8px;
}

:deep(.el-upload-dragger) {
  padding: 40px;
}

.el-icon--upload {
  font-size: 67px;
  color: var(--primary-color);
  margin-bottom: 16px;
}
</style>
