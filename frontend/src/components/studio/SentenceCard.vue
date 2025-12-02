<template>
  <el-card
    class="sentence-card"
    shadow="hover"
  >
    <template #header>
      <div class="card-header">
        <span class="card-index">#{{ index + 1 }}</span>
        <div class="header-actions">
          <el-tag 
            v-if="sentence.image_prompt" 
            size="small" 
            type="info" 
            effect="plain"
            class="clickable-tag"
            @click="handlePreview('prompt')"
          >
            <el-icon><Document /></el-icon>
            提示词
          </el-tag>
          <el-tag 
            v-if="sentence.image_url" 
            size="small" 
            type="success" 
            effect="plain"
            class="clickable-tag"
            @click="handlePreview('image')"
          >
            <el-icon><Picture /></el-icon>
            图片
          </el-tag>
          <el-tag 
            v-if="sentence.audio_url" 
            size="small" 
            type="warning" 
            effect="plain"
            class="clickable-tag"
            @click="handlePreview('audio')"
          >
            <el-icon><Microphone /></el-icon>
            音频
          </el-tag>
          <el-dropdown @command="handlePromptAction" trigger="click">
            <span class="el-dropdown-link">
              <el-icon><MoreFilled /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="view">查看提示词</el-dropdown-item>
                <el-dropdown-item command="edit">编辑提示词</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </div>
    </template>
    
    <div class="card-content">
      <p class="sentence-text">{{ sentence.content }}</p>
    </div>
    
    <div class="card-actions">
      <el-tooltip content="重新生成提示词" placement="top" :show-after="500">
        <el-button
          class="action-btn"
          :class="{ 'has-content': sentence.image_prompt }"
          :loading="loadingStates.generatingPrompt"
          @click="handleRegeneratePrompt"
          text
        >
          <el-icon><MagicStick /></el-icon>
        </el-button>
      </el-tooltip>
      
      <el-tooltip content="生成图片" placement="top" :show-after="500">
        <el-button
          class="action-btn"
          :class="{ 'has-content': sentence.image_url }"
          :loading="loadingStates.generatingImage"
          :disabled="!sentence.image_prompt"
          @click="handleGenerateImage"
          text
        >
          <el-icon><Picture /></el-icon>
        </el-button>
      </el-tooltip>
      
      <el-tooltip content="生成音频" placement="top" :show-after="500">
        <el-button
          class="action-btn"
          :class="{ 'has-content': sentence.audio_url }"
          :loading="loadingStates.generatingAudio"
          :disabled="!sentence.image_prompt"
          @click="handleGenerateAudio"
          text
        >
          <el-icon><Microphone /></el-icon>
        </el-button>
      </el-tooltip>
    </div>
  </el-card>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'
import { MoreFilled, MagicStick, Microphone, Picture, Document } from '@element-plus/icons-vue'

const props = defineProps({
  sentence: {
    type: Object,
    required: true
  },
  index: {
    type: Number,
    required: true
  },
  loadingStates: {
    type: Object,
    default: () => ({
      generatingPrompt: false,
      generatingAudio: false,
      generatingImage: false
    })
  }
})

const emit = defineEmits(['prompt-action', 'regenerate-prompt', 'regenerate-image', 'generate-audio', 'update:loadingStates', 'preview'])

// 处理提示词操作（查看/编辑）
const handlePromptAction = async (action) => {
  emit('prompt-action', {
    action,
    sentence: props.sentence
  })
}

// 处理重新生成提示词
const handleRegeneratePrompt = () => {
  emit('regenerate-prompt', props.sentence)
}

// 处理生成音频
const handleGenerateAudio = () => {
  emit('generate-audio', props.sentence)
}

// 处理生成图片
const handleGenerateImage = () => {
  emit('regenerate-image', props.sentence)
}

// 处理预览
const handlePreview = (type) => {
  let content = ''
  
  switch(type) {
    case 'prompt':
      content = props.sentence.image_prompt
      break
    case 'image':
      content = props.sentence.image_url
      break
    case 'audio':
      content = props.sentence.audio_url
      break
  }
  
  emit('preview', { type, content })
}
</script>

<style scoped>
/* 卡片基础样式 */
.sentence-card {
  background: #ffffff;
  border: 1px solid var(--border-primary);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition: all var(--transition-normal);
  display: flex;
  flex-direction: column;
}

.sentence-card:hover {
  border-color: var(--primary-color);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

/* 卡片头部样式 */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-md) var(--space-lg);
  background: var(--bg-secondary);
  border-bottom: 1px solid var(--border-primary);
}

.card-index {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.header-actions {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}

/* 可点击标签样式 */
.clickable-tag {
  cursor: pointer;
  transition: all var(--transition-fast);
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.clickable-tag:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
  opacity: 0.8;
}

/* 下拉菜单样式 */
.el-dropdown-link {
  color: var(--text-tertiary);
  cursor: pointer;
  padding: 4px;
  border-radius: var(--radius-base);
  transition: all var(--transition-fast);
  display: flex;
  align-items: center;
  justify-content: center;
}

.el-dropdown-link:hover {
  color: var(--primary-color);
  background: var(--bg-tertiary);
}

/* 卡片内容样式 */
.card-content {
  padding: var(--space-lg);
  flex: 1;
}

.sentence-text {
  color: var(--text-primary);
  font-size: var(--text-base);
  line-height: var(--leading-relaxed);
  margin: 0;
  white-space: pre-wrap;
}

/* 卡片操作区域样式 */
.card-actions {
  display: flex;
  justify-content: space-around;
  padding: var(--space-sm) var(--space-lg);
  background: var(--bg-primary);
  border-top: 1px solid var(--border-primary);
}

.action-btn {
  flex: 1;
  height: 40px;
  font-size: 18px;
  color: var(--text-tertiary);
  border-radius: var(--radius-base);
  transition: all var(--transition-fast);
}

.action-btn:hover:not(:disabled) {
  background: var(--bg-secondary);
  color: var(--primary-color);
}

.action-btn.has-content {
  color: var(--primary-color);
}

.action-btn:disabled {
  color: var(--text-disabled);
  cursor: not-allowed;
}
</style>