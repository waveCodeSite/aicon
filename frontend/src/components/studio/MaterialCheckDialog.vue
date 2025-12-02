<template>
  <el-dialog
    v-model="dialogVisible"
    title="素材检测结果"
    width="600px"
    :close-on-click-modal="false"
  >
    <div v-loading="loading" class="check-result">
      <template v-if="!loading && result">
        <!-- 成功状态 -->
        <div v-if="result.all_ready" class="success-state">
          <el-result
            icon="success"
            title="素材准备完成"
            sub-title="所有句子的素材都已准备就绪，可以生成视频了！"
          >
            <template #extra>
              <el-descriptions :column="2" border>
                <el-descriptions-item label="总句子数">
                  {{ result.total_sentences }}
                </el-descriptions-item>
                <el-descriptions-item label="已准备">
                  <el-tag type="success">{{ result.ready_count }}</el-tag>
                </el-descriptions-item>
                <el-descriptions-item label="章节状态">
                  <el-tag type="success">{{ getStatusText(result.chapter_status) }}</el-tag>
                </el-descriptions-item>
              </el-descriptions>
            </template>
          </el-result>
        </div>

        <!-- 未完成状态 -->
        <div v-else class="incomplete-state">
          <el-result
            icon="warning"
            title="素材未完成"
            :sub-title="`还有 ${result.total_sentences - result.ready_count} 个句子的素材未准备好`"
          >
            <template #extra>
              <div class="stats-section">
                <el-descriptions :column="2" border>
                  <el-descriptions-item label="总句子数">
                    {{ result.total_sentences }}
                  </el-descriptions-item>
                  <el-descriptions-item label="已准备">
                    <el-tag type="success">{{ result.ready_count }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="缺少提示词">
                    <el-tag type="warning">{{ result.missing_materials.prompts }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="缺少图片">
                    <el-tag type="warning">{{ result.missing_materials.images }}</el-tag>
                  </el-descriptions-item>
                  <el-descriptions-item label="缺少音频">
                    <el-tag type="warning">{{ result.missing_materials.audio }}</el-tag>
                  </el-descriptions-item>
                </el-descriptions>
              </div>

              <!-- 缺失素材详情 -->
              <div v-if="result.missing_sentences.length > 0" class="missing-details">
                <el-divider content-position="left">缺失素材详情</el-divider>
                <div class="missing-list">
                  <el-card
                    v-for="(item, index) in result.missing_sentences"
                    :key="item.sentence_id"
                    class="missing-item"
                    shadow="hover"
                  >
                    <div class="item-header">
                      <span class="item-index">#{{ index + 1 }}</span>
                      <div class="item-tags">
                        <el-tag
                          v-for="missing in item.missing"
                          :key="missing"
                          size="small"
                          type="danger"
                          effect="plain"
                        >
                          {{ getMaterialText(missing) }}
                        </el-tag>
                      </div>
                    </div>
                    <div class="item-content">{{ item.content }}</div>
                  </el-card>
                </div>
              </div>
            </template>
          </el-result>
        </div>
      </template>
    </div>

    <template #footer>
      <el-button @click="handleClose">关闭</el-button>
      <el-button v-if="result && !result.all_ready" type="primary" @click="handleGenerate">
        去生成素材
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    required: true
  },
  loading: {
    type: Boolean,
    default: false
  },
  result: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['update:visible', 'generate'])

const dialogVisible = computed({
  get: () => props.visible,
  set: (val) => emit('update:visible', val)
})

const handleClose = () => {
  emit('update:visible', false)
}

const handleGenerate = () => {
  emit('generate')
  handleClose()
}

const getMaterialText = (type) => {
  const map = {
    'prompt': '提示词',
    'image': '图片',
    'audio': '音频'
  }
  return map[type] || type
}

const getStatusText = (status) => {
  const map = {
    'pending': '待处理',
    'confirmed': '已确认',
    'generating_prompts': '生成提示词中',
    'generated_prompts': '提示词已生成',
    'materials_prepared': '素材已准备',
    'generating_video': '生成视频中',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return map[status] || status
}
</script>

<style scoped>
.check-result {
  min-height: 200px;
}

.success-state,
.incomplete-state {
  padding: var(--space-md);
}

.stats-section {
  margin-bottom: var(--space-lg);
}

.missing-details {
  margin-top: var(--space-lg);
}

.missing-list {
  max-height: 400px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
}

.missing-item {
  background: var(--bg-primary);
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: var(--space-sm);
}

.item-index {
  font-size: var(--text-sm);
  font-weight: 600;
  color: var(--text-secondary);
  font-family: var(--font-mono);
}

.item-tags {
  display: flex;
  gap: var(--space-xs);
}

.item-content {
  color: var(--text-primary);
  font-size: var(--text-sm);
  line-height: var(--leading-relaxed);
}

/* 滚动条样式 */
.missing-list::-webkit-scrollbar {
  width: 6px;
}

.missing-list::-webkit-scrollbar-track {
  background: var(--bg-secondary);
  border-radius: 3px;
}

.missing-list::-webkit-scrollbar-thumb {
  background: var(--border-primary);
  border-radius: 3px;
}

.missing-list::-webkit-scrollbar-thumb:hover {
  background: var(--text-tertiary);
}
</style>
