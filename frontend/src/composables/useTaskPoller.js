import { ref, onUnmounted } from 'vue'
import api from '@/services/api'
import { ElMessage } from 'element-plus'

export function useTaskPoller() {
  const taskStatus = ref(null)
  const isPolling = ref(false)
  const pollInterval = ref(null)
  const taskResult = ref(null)

  const stopPolling = () => {
    if (pollInterval.value) {
      clearInterval(pollInterval.value)
      pollInterval.value = null
    }
    isPolling.value = false
  }

  const startPolling = (taskId, onSuccess = null, onError = null) => {
    if (!taskId) return

    stopPolling()
    isPolling.value = true
    taskStatus.value = 'PENDING'

    pollInterval.value = setInterval(async () => {
      try {
        const response = await api.get(`/tasks/${taskId}`)
        taskStatus.value = response.status
        
        if (response.status === 'SUCCESS') {
          taskResult.value = response.result
          stopPolling()
          if (onSuccess) onSuccess(response.result)
        } else if (response.status === 'FAILURE' || response.status === 'REVOKED') {
          stopPolling()
          if (onError) onError(response)
          else ElMessage.error('任务执行失败')
        }
      } catch (error) {
        console.error('Task polling error:', error)
        stopPolling()
        if (onError) onError(error)
      }
    }, 2000) // Poll every 2 seconds
  }

  onUnmounted(() => {
    stopPolling()
  })

  return {
    taskStatus,
    isPolling,
    taskResult,
    startPolling,
    stopPolling
  }
}
