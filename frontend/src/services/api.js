import axios from 'axios'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '@/stores/auth'
import router from '@/router'

// 创建axios实例
const api = axios.create({
  baseURL: '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    // 添加认证token
    const authStore = useAuthStore()
    if (authStore.token) {
      config.headers.Authorization = `Bearer ${authStore.token}`
    }

    return config
  },
  (error) => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  async (error) => {
    const { response, config } = error

    if (response) {
      const { status, data } = response

      switch (status) {
        case 401:
          // 检查是否是登录或刷新接口
          if (config.url && (config.url.includes('/auth/login') || config.url.includes('/auth/refresh'))) {
            ElMessage.error(data.detail || '认证失败')
          } else {
            // 尝试刷新token
            const authStore = useAuthStore()
            try {
              await authStore.refresh()
              // 重试原请求
              return api.request(config)
            } catch (refreshError) {
              // 刷新失败，登出
              authStore.logout()
              router.push({ name: 'Login', query: { redirect: router.currentRoute.value.fullPath } })
              ElMessage.error('登录已过期，请重新登录')
            }
          }
          break

        case 403:
          ElMessage.error('没有权限访问此资源')
          break

        case 404:
          ElMessage.error('请求的资源不存在')
          break

        case 400:
          // 业务错误
          error.message = data.message
          break

        case 422:
          // 表单验证错误
          if (data.detail && Array.isArray(data.detail)) {
            const errors = data.detail.map(item => item.msg).join(', ')
            ElMessage.error(errors)
          } else {
            ElMessage.error(data.detail || '请求参数有误')
          }
          break

        case 500:
          ElMessage.error('服务器内部错误，请稍后重试')
          break

        default:
          ElMessage.error(data.detail || `请求失败 (${status})`)
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络连接')
    } else {
      ElMessage.error('网络错误，请检查网络连接')
    }

    return Promise.reject(error)
  }
)

// 导出常用的请求方法
export const get = (url, config) => api.get(url, config)
export const post = (url, data, config) => api.post(url, data, config)
export const put = (url, data, config) => api.put(url, data, config)
export const del = (url, config) => api.delete(url, config)
export const patch = (url, data, config) => api.patch(url, data, config)

// 文件上传方法
export const upload = (url, data, config = {}) => {
  // 如果data是FormData对象，直接使用
  // 如果是File对象，包装成FormData
  let formData
  if (data instanceof FormData) {
    formData = data
  } else {
    formData = new FormData()
    formData.append('file', data)
  }

  const uploadConfig = {
    timeout: 5 * 60 * 1000, // 大文件上传超时5分钟
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: config.onUploadProgress,
    ...config
  }

  return api.post(url, formData, uploadConfig)
}

// 导出axios实例
export default api