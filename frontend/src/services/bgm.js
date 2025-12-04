/**
 * BGM API服务
 */

import request from '@/utils/request'

/**
 * 上传BGM文件
 * @param {File} file - BGM文件
 * @param {string} name - BGM名称
 * @returns {Promise}
 */
export function uploadBGM(file, name) {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)

    return request({
        url: '/bgms/upload',
        method: 'post',
        data: formData,
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    })
}

/**
 * 获取BGM列表
 * @param {Object} params - 查询参数
 * @returns {Promise}
 */
export function getBGMs(params = {}) {
    return request({
        url: '/bgms/',
        method: 'get',
        params
    })
}

/**
 * 获取BGM详情
 * @param {string} id - BGM ID
 * @returns {Promise}
 */
export function getBGMById(id) {
    return request({
        url: `/bgms/${id}`,
        method: 'get'
    })
}

/**
 * 删除BGM
 * @param {string} id - BGM ID
 * @returns {Promise}
 */
export function deleteBGM(id) {
    return request({
        url: `/bgms/${id}`,
        method: 'delete'
    })
}

/**
 * 获取BGM统计信息
 * @returns {Promise}
 */
export function getBGMStats() {
    return request({
        url: '/bgms/stats',
        method: 'get'
    })
}

export default {
    uploadBGM,
    getBGMs,
    getBGMById,
    deleteBGM,
    getBGMStats
}
