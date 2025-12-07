/**
 * 管理员 API 服务
 */

import api from './api'

const adminService = {
  /**
   * 获取用户列表
   */
  async getUsers(params = {}) {
    return await api.get('/admin/users', { params })
  },

  /**
   * 获取用户详情
   */
  async getUser(userId) {
    return await api.get(`/admin/users/${userId}`)
  },

  /**
   * 更新用户
   */
  async updateUser(userId, data) {
    return await api.put(`/admin/users/${userId}`, data)
  },

  /**
   * 创建用户
   */
  async createUser(data) {
    return await api.post('/admin/users', data)
  },

  /**
   * 删除用户
   */
  async deleteUser(userId) {
    return await api.delete(`/admin/users/${userId}`)
  },

  /**
   * 切换用户激活状态
   */
  async toggleUserActive(userId) {
    return await api.post(`/admin/users/${userId}/toggle-active`)
  },

  // 存储源管理
  async getStorageSources() {
    return await api.get('/admin/storage/sources')
  },

  async createStorageSource(data) {
    return await api.post('/admin/storage/sources', data)
  },

  async updateStorageSource(id, data) {
    return await api.put(`/admin/storage/sources/${id}`, data)
  },

  async deleteStorageSource(id) {
    return await api.delete(`/admin/storage/sources/${id}`)
  },

  async activateStorageSource(id) {
    return await api.post(`/admin/storage/sources/${id}/activate`)
  },

  async deactivateStorageSource(id) {
    return await api.post(`/admin/storage/sources/${id}/deactivate`)
  },

  async testStorageConnection(data) {
    return await api.post('/admin/storage/sources/test', data)
  },

  // 存储文件管理
  async listStorageFiles(sourceId, prefix = '', limit = 100) {
    return await api.get(`/admin/storage/sources/${sourceId}/files`, {
      params: { prefix, limit }
    })
  },

  async deleteStorageFile(sourceId, key) {
    return await api.delete(`/admin/storage/sources/${sourceId}/files`, {
      params: { key }
    })
  }
}

export default adminService
