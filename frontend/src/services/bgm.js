/**
 * BGM管理服务
 */

import { get, post, del } from './api'

/**
 * BGM管理服务
 */
export const bgmService = {
    /**
     * 上传BGM文件
     * @param {File} file - BGM文件
     * @param {string} name - BGM名称
     * @returns {Promise} 上传结果
     */
    async uploadBGM(file, name) {
        const formData = new FormData()
        formData.append('file', file)
        formData.append('name', name)

        return await post('/bgms/upload', formData, {
            headers: {
                'Content-Type': 'multipart/form-data'
            }
        })
    },

    /**
     * 获取BGM列表
     * @param {Object} params - 查询参数
     * @param {number} params.page - 页码
     * @param {number} params.size - 每页大小
     * @param {string} params.sort_by - 排序字段
     * @param {string} params.sort_order - 排序顺序
     * @returns {Promise} BGM列表和总数
     */
    async getBGMs(params = {}) {
        return await get('/bgms/', { params })
    },

    /**
     * 根据ID获取BGM详情
     * @param {string} id - BGM ID
     * @returns {Promise} BGM详情
     */
    async getBGM(id) {
        return await get(`/bgms/${id}`)
    },

    /**
     * 删除BGM
     * @param {string} id - BGM ID
     * @returns {Promise} 删除结果
     */
    async deleteBGM(id) {
        return await del(`/bgms/${id}`)
    },

    /**
     * 获取BGM统计信息
     * @returns {Promise} 统计信息
     */
    async getBGMStats() {
        return await get('/bgms/stats')
    }
}

export default bgmService
