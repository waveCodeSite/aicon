import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/services/api'

export const useSystemStore = defineStore('system', () => {
  const allowRegistration = ref(true)
  const loading = ref(false)

  // 从后端获取系统设置
  const fetchSettings = async () => {
    loading.value = true
    try {
      const data = await api.get('/admin/settings')
      allowRegistration.value = data.allow_registration ?? true
    } catch {
      // 如果获取失败，使用默认值
    } finally {
      loading.value = false
    }
  }

  // 更新系统设置
  const updateSettings = async (settings) => {
    const data = await api.put('/admin/settings', settings)
    if (settings.allow_registration !== undefined) {
      allowRegistration.value = settings.allow_registration
    }
    return data
  }

  return {
    allowRegistration,
    loading,
    fetchSettings,
    updateSettings
  }
})
