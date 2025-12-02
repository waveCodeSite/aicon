<template>
  <el-dialog
    v-model="dialogVisible"
    :title="dialogTitle"
    width="800px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="preview-content">
      <!-- 提示词预览 -->
      <div v-if="type === 'prompt'" class="prompt-preview">
        <el-input
          :model-value="content"
          type="textarea"
          :rows="10"
          readonly
          placeholder="暂无提示词"
        />
      </div>

      <!-- 图片预览 -->
      <div v-else-if="type === 'image'" class="image-preview">
        <el-image
          v-if="content"
          :src="content"
          fit="contain"
          :preview-src-list="[content]"
          class="preview-image"
        >
          <template #error>
            <div class="image-error">
              <el-icon><Picture /></el-icon>
              <span>图片加载失败</span>
            </div>
          </template>
        </el-image>
        <el-empty v-else description="暂无图片" />
      </div>

      <!-- 音频预览 -->
      <div v-else-if="type === 'audio'" class="audio-preview">
        <div v-if="content" class="audio-player">
          <audio
            ref="audioPlayer"
            :src="content"
            controls
            controlsList="nodownload"
            class="audio-element"
          >
            您的浏览器不支持音频播放
          </audio>
          <div class="audio-info">
            <el-icon><Microphone /></el-icon>
            <span>{{ content }}</span>
          </div>
        </div>
        <el-empty v-else description="暂无音频" />
      </div>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button v-if="content && type === 'image'" type="primary" @click="handleDownload">
        <el-icon><Download /></el-icon>
        下载图片
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, ref, watch } from 'vue'
import { Picture, Microphone, Download } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  type: {
    type: String,
    required: true,
    validator: (value) => ['prompt', 'image', 'audio'].includes(value)
  },
  content: {
    type: String,
    default: ''
  },
  title: {
    type: String,
    default: ''
  }
})

const emit = defineEmits(['update:visible'])

const audioPlayer = ref(null)

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const dialogTitle = computed(() => {
  if (props.title) return props.title
  
  const titleMap = {
    'prompt': '提示词预览',
    'image': '图片预览',
    'audio': '音频预览'
  }
  return titleMap[props.type] || '预览'
})

const handleClose = () => {
  // 停止音频播放
  if (audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.currentTime = 0
  }
  emit('update:visible', false)
}

const handleDownload = () => {
  if (!props.content) return
  
  try {
    const link = document.createElement('a')
    link.href = props.content
    link.download = `image_${Date.now()}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    ElMessage.success('下载成功')
  } catch (error) {
    ElMessage.error('下载失败')
  }
}

// 监听对话框关闭，停止音频播放
watch(() => props.visible, (newVal) => {
  if (!newVal && audioPlayer.value) {
    audioPlayer.value.pause()
    audioPlayer.value.currentTime = 0
  }
})
</script>

<style scoped>
.preview-content {
  min-height: 300px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 提示词预览样式 */
.prompt-preview {
  width: 100%;
}

.prompt-preview :deep(.el-textarea__inner) {
  font-family: var(--font-mono);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

/* 图片预览样式 */
.image-preview {
  width: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.preview-image {
  max-width: 100%;
  max-height: 600px;
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-md);
}

.image-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--space-sm);
  color: var(--text-tertiary);
  padding: var(--space-xl);
}

.image-error .el-icon {
  font-size: 48px;
}

/* 音频预览样式 */
.audio-preview {
  width: 100%;
}

.audio-player {
  display: flex;
  flex-direction: column;
  gap: var(--space-md);
  align-items: center;
}

.audio-element {
  width: 100%;
  max-width: 500px;
  outline: none;
}

.audio-info {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  color: var(--text-secondary);
  font-size: var(--text-sm);
  word-break: break-all;
  padding: 0 var(--space-md);
}

.audio-info .el-icon {
  font-size: 18px;
  flex-shrink: 0;
}
</style>
