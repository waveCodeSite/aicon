import api from './api'

/**
 * 段落管理服务
 */
export const paragraphsService = {
    /**
     * 获取章节的段落列表
     * @param {string} chapterId 章节ID
     * @returns {Promise<Object>}
     */
    async getParagraphs(chapterId) {
        return await api.get(`/paragraphs/chapters/${chapterId}/paragraphs`)
    },

    /**
     * 获取单个段落详情
     * @param {string} paragraphId 段落ID
     * @returns {Promise<Object>}
     */
    async getParagraph(paragraphId) {
        return await api.get(`/paragraphs/${paragraphId}`)
    },

    /**
     * 创建新段落
     * @param {string} chapterId 章节ID
     * @param {Object} paragraphData 段落数据
     * @returns {Promise<Object>}
     */
    async createParagraph(chapterId, paragraphData) {
        return await api.post(`/paragraphs/chapters/${chapterId}/paragraphs`, paragraphData)
    },

    /**
     * 更新段落
     * @param {string} paragraphId 段落ID
     * @param {Object} paragraphData 段落数据
     * @returns {Promise<Object>}
     */
    async updateParagraph(paragraphId, paragraphData) {
        const response = await api.put(`/paragraphs/${paragraphId}`, paragraphData)
        return response.data
    },

    /**
     * 批量更新段落
     * @param {string} chapterId 章节ID
     * @param {Object} data 包含paragraphs数组的数据对象
     * @returns {Promise<Object>}
     */
    async batchUpdateParagraphs(chapterId, data) {
        const response = await api.put(`/paragraphs/chapters/${chapterId}/paragraphs/batch`, data)
        return response.data
    },

    /**
     * 删除段落
     * @param {string} paragraphId 段落ID
     * @returns {Promise<Object>}
     */
    async deleteParagraph(paragraphId) {
        return await api.delete(`/paragraphs/${paragraphId}`)
    }
}

export default paragraphsService
