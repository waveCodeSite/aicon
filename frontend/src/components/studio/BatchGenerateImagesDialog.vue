<template>
  <el-dialog
    v-model="dialogVisible"
    title="批量生成图片"
    width="500px"
  >
    <el-form :inline="false" class="dialog-form">
      <el-form-item label="API Key" style="width: 100%">
        <el-select v-model="selectedApiKey" placeholder="选择API Key" style="width: 100%">
          <el-option
            v-for="key in apiKeys"
            :key="key.id"
            :label="`${key.name} (${key.provider})`"
            :value="key.id"
          />
        </el-select>
      </el-form-item>
      
      <el-form-item label="模型" style="width: 100%">
        <el-select 
          v-model="selectedModel" 
          placeholder="选择模型" 
          style="width: 100%"
          :loading="loadingModels"
          filterable
          allow-create
          default-first-option
        >
          <el-option
            v-for="model in modelOptions"
            :key="model"
            :label="model"
            :value="model"
          />
        </el-select>
      </el-form-item>
    </el-form>
    
    <template #footer>
      <span class="dialog-footer">
        <el-button @click="handleCancel">取消</el-button>
        <el-button type="primary" :loading="generating" @click="handleGenerate">
          生成
        </el-button>
      </span>
    </template>
  </el-dialog>
</template>

<script setup>
import { ref, defineProps, defineEmits, watch } from 'vue'
import { ElMessage } from 'element-plus'
import api from '@/services/api'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  sentencesIds: {
    type: [Array, String],
    required: true
  },
  apiKeys: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:visible', 'generate-success'])

const dialogVisible = ref(props.visible)
const selectedApiKey = ref('')
const selectedModel = ref('')
const modelOptions = ref([])
const loadingModels = ref(false)
const generating = ref(false)

// 监听visible prop变化，更新dialogVisible
watch(() => props.visible, (newValue) => {
  dialogVisible.value = newValue
})

// 监听selectedApiKey变化，获取可用模型
watch(selectedApiKey, async (newKeyId) => {
  if (!newKeyId) {
    modelOptions.value = []
    selectedModel.value = ''
    return
  }
  
  loadingModels.value = true
  try {
    const models = await api.get(`/api-keys/${newKeyId}/models?type=image`)
    modelOptions.value = models || []
    // 如果有模型，自动选择第一个
    if (modelOptions.value.length > 0) {
      selectedModel.value = modelOptions.value[0]
    } else {
      selectedModel.value = ''
    }
  } catch (error) {
    console.error('获取模型列表失败', error)
    ElMessage.warning('获取模型列表失败')
    modelOptions.value = []
    selectedModel.value = ''
  } finally {
    loadingModels.value = false
  }
})

// 更新visible状态并通知父组件
const updateDialogVisible = (newValue) => {
  dialogVisible.value = newValue
  emit('update:visible', newValue)
}

// 处理取消
const handleCancel = () => {
  updateDialogVisible(false)
  resetForm()
}

// 重置表单
const resetForm = () => {
  selectedApiKey.value = ''
  selectedModel.value = ''
  modelOptions.value = []
}

// 处理批量生成图片
const handleGenerate = async () => {
  if (!selectedApiKey.value) {
    ElMessage.warning('请选择API Key')
    return
  }
  
  generating.value = true
  try {
    const ids = Array.isArray(props.sentencesIds) ? props.sentencesIds : [props.sentencesIds]
    const response = await api.post('/image/generate-images', {
      sentences_ids: ids,
      api_key_id: selectedApiKey.value,
      model: selectedModel.value || null
    })
    
    if (response.success) {
      ElMessage.success(response.message)
      updateDialogVisible(false)
      emit('generate-success', response.task_id)
      resetForm()
    }
  } catch (error) {
    console.error('批量生成图片失败', error)
    ElMessage.error('批量生成图片失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.dialog-form {
  margin-bottom: 0;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}
</style>