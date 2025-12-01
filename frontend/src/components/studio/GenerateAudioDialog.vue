<template>
  <el-dialog
    v-model="dialogVisible"
    title="生成音频"
    width="500px"
  >
    <el-form :inline="false" class="dialog-form" label-width="80px">
      <el-form-item label="API Key">
        <el-select v-model="selectedApiKey" placeholder="选择API Key" style="width: 100%">
          <el-option
            v-for="key in apiKeys"
            :key="key.id"
            :label="`${key.name} (${key.provider})`"
            :value="key.id"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="语音风格">
        <el-select 
          v-model="voice" 
          placeholder="选择语音风格" 
          style="width: 100%"
          filterable
          allow-create
          default-first-option
        >
          <el-option
            v-for="voiceOption in voiceOptions"
            :key="voiceOption.value"
            :label="voiceOption.label"
            :value="voiceOption.value"
          />
        </el-select>
      </el-form-item>

      <el-form-item label="模型">
        <el-select 
          v-model="model" 
          placeholder="选择模型" 
          style="width: 100%"
          :loading="loadingModels"
          filterable
          allow-create
          default-first-option
        >
          <el-option
            v-for="modelOption in modelOptions"
            :key="modelOption"
            :label="modelOption"
            :value="modelOption"
          />
        </el-select>
      </el-form-item>

      <div class="info-text">
        即将为 {{ sentencesCount }} 个句子生成音频。
      </div>
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
import { ref, defineProps, defineEmits, watch, computed } from 'vue'
import { ElMessage } from 'element-plus'
import audioService from '@/services/audio'
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
const voice = ref('alloy')
const model = ref('tts-1')
const modelOptions = ref([])
const loadingModels = ref(false)
const voiceOptions = ref([])
const generating = ref(false)

// 默认语音选项（OpenAI 风格）
const defaultVoiceOptions = [
  { label: 'Alloy (通用)', value: 'alloy' },
  { label: 'Echo (男声)', value: 'echo' },
  { label: 'Fable (男声)', value: 'fable' },
  { label: 'Onyx (深沉男声)', value: 'onyx' },
  { label: 'Nova (女声)', value: 'nova' },
  { label: 'Shimmer (清脆女声)', value: 'shimmer' }
]

// 硅基流动预置语音（格式：模型:音色）
const getSiliconFlowVoiceOptions = (model) => {
  const baseModel = model || 'FunAudioLLM/CosyVoice2-0.5B'
  return [
    { label: '沉稳男声 (alex)', value: `${baseModel}:alex` },
    { label: '低沉男声 (benjamin)', value: `${baseModel}:benjamin` },
    { label: '磁性男声 (charles)', value: `${baseModel}:charles` },
    { label: '欢快男声 (david)', value: `${baseModel}:david` },
    { label: '沉稳女声 (anna)', value: `${baseModel}:anna` },
    { label: '激情女声 (bella)', value: `${baseModel}:bella` },
    { label: '温柔女声 (claire)', value: `${baseModel}:claire` },
    { label: '欢快女声 (diana)', value: `${baseModel}:diana` }
  ]
}

const sentencesCount = computed(() => {
  return Array.isArray(props.sentencesIds) ? props.sentencesIds.length : 1
})

// 监听visible prop变化，更新dialogVisible
watch(() => props.visible, (newValue) => {
  dialogVisible.value = newValue
})

// 监听selectedApiKey变化，获取可用模型
watch(selectedApiKey, async (newKeyId) => {
  if (!newKeyId) {
    modelOptions.value = []
    model.value = 'tts-1'
    voiceOptions.value = defaultVoiceOptions
    voice.value = 'alloy'
    return
  }
  
  // 检查是否是硅基流动
  const selectedKey = props.apiKeys.find(k => k.id === newKeyId)
  const isSiliconFlow = selectedKey?.provider?.toLowerCase() === 'siliconflow'
  
  loadingModels.value = true
  try {
    const models = await api.get(`/api-keys/${newKeyId}/models?type=audio`)
    modelOptions.value = models || []
    // 如果有模型，自动选择第一个
    if (modelOptions.value.length > 0) {
      model.value = modelOptions.value[0]
    } else {
      model.value = 'tts-1'
    }
    
    // 根据供应商设置语音选项
    if (isSiliconFlow) {
      voiceOptions.value = getSiliconFlowVoiceOptions(model.value)
      voice.value = voiceOptions.value[0].value
    } else {
      voiceOptions.value = defaultVoiceOptions
      voice.value = 'alloy'
    }
  } catch (error) {
    console.error('获取模型列表失败', error)
    ElMessage.warning('获取模型列表失败')
    modelOptions.value = []
    model.value = 'tts-1'
    voiceOptions.value = defaultVoiceOptions
    voice.value = 'alloy'
  } finally {
    loadingModels.value = false
  }
})

// 监听模型变化，更新硅基流动的语音选项
watch(model, (newModel) => {
  const selectedKey = props.apiKeys.find(k => k.id === selectedApiKey.value)
  const isSiliconFlow = selectedKey?.provider?.toLowerCase() === 'siliconflow'
  
  if (isSiliconFlow && newModel) {
    voiceOptions.value = getSiliconFlowVoiceOptions(newModel)
    voice.value = voiceOptions.value[0].value
  }
})

// 监听dialogVisible变化，通知父组件
watch(dialogVisible, (newValue) => {
  emit('update:visible', newValue)
})

// 更新visible状态并通知父组件
const updateDialogVisible = (newValue) => {
  dialogVisible.value = newValue
}

// 处理取消
const handleCancel = () => {
  updateDialogVisible(false)
  resetForm()
}

// 重置表单
const resetForm = () => {
  selectedApiKey.value = ''
  voice.value = 'alloy'
  model.value = 'tts-1'
  modelOptions.value = []
  voiceOptions.value = defaultVoiceOptions
}

// 处理生成音频
const handleGenerate = async () => {
  if (!selectedApiKey.value) {
    ElMessage.warning('请选择API Key')
    return
  }
  
  generating.value = true
  try {
    const ids = Array.isArray(props.sentencesIds) ? props.sentencesIds : [props.sentencesIds]
    const response = await audioService.generateAudio({
      sentences_ids: ids,
      api_key_id: selectedApiKey.value,
      voice: voice.value,
      model: model.value
    })
    
    if (response.success) {
      ElMessage.success(response.message)
      updateDialogVisible(false)
      emit('generate-success', response.task_id)
      // resetForm() // 成功后不重置，方便下次使用相同配置
    }
  } catch (error) {
    console.error('生成音频失败', error)
    ElMessage.error('生成音频失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generating.value = false
  }
}
</script>

<style scoped>
.dialog-form {
  margin-bottom: 0;
}

.info-text {
  margin-top: 10px;
  color: #909399;
  font-size: 14px;
  text-align: center;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: var(--space-sm);
}
</style>
