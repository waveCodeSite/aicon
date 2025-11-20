import api from './api'

/**
 * 章节管理服务
 */
export const chaptersService = {
  /**
   * 获取章节列表
   * @param {string} projectId 项目ID
   * @param {Object} params 查询参数
   * @returns {Promise<Object>}
   */
  async getChapters(projectId, params = {}) {
    return await api.get('/chapters/', {
      params: {
        project_id: projectId,
        ...params
      }
    })
  },

  /**
   * 获取单个章节详情
   * @param {string} chapterId 章节ID
   * @returns {Promise<Object>}
   */
  async getChapter(chapterId) {
    return await api.get(`/chapters/${chapterId}`)
  },

  /**
   * 创建章节
   * @param {string} projectId 项目ID
   * @param {Object} chapterData 章节数据
   * @returns {Promise<Object>}
   */
  async createChapter(projectId, chapterData) {
    return await api.post('/chapters/', chapterData, {
      params: { project_id: projectId }
    })
  },

  /**
   * 更新章节
   * @param {string} chapterId 章节ID
   * @param {Object} chapterData 章节数据
   * @returns {Promise<Object>}
   */
  async updateChapter(chapterId, chapterData) {
    const response = await api.put(`/chapters/${chapterId}`, chapterData)
    return response.data
  },

  /**
   * 删除章节
   * @param {string} chapterId 章节ID
   * @returns {Promise<Object>}
   */
  async deleteChapter(chapterId) {
    return await api.delete(`/chapters/${chapterId}`)
  }
}

export default chaptersService