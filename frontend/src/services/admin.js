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
  }
}

export default adminService
