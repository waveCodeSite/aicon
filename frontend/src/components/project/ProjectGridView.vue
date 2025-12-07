<template>
  <div class="grid-view">
    <el-row :gutter="20">
      <el-col
        v-for="project in projects"
        :key="project.id"
        :xs="24"
        :sm="12"
        :md="8"
        :lg="6"
        :xl="4"
      >
        <ProjectCard
          :project="project"
          @view="$emit('view-project', $event)"
          @delete="$emit('delete-project', $event)"
        />
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import ProjectCard from './ProjectCard.vue'

defineProps({
  projects: {
    type: Array,
    default: () => [],
  }
})

defineEmits(['view-project', 'delete-project'])
</script>

<style scoped>
.grid-view {
  width: 100%;
  overflow: visible;
  padding: var(--space-lg) 0;
}

.grid-view .el-col {
  padding: var(--space-lg);
}

:deep(.el-row) {
  width: 100%;
  margin: 0;
  display: flex;
  flex-wrap: wrap;
}

:deep(.el-col) {
  position: relative;
  overflow: visible;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .grid-view {
    width: 100%;
    overflow: visible;
  }

  .grid-view .el-col {
    padding: var(--space-sm);
  }
}
</style>
