/**
 * BGM管理 Composable
 */

import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import bgmService from '@/services/bgm'

export function useBGM() {
    // 状态
    const bgms = ref([])
    const loading = ref(false)
    const stats = ref({
        total_count: 0,
        total_size: 0,
        total_size_mb: 0
    })
    const pagination = ref({
        page: 1,
        size: 20,
        total: 0,
        total_pages: 0
    })

    // 计算属性
    const hasBGMs = computed(() => bgms.value.length > 0)

    /**
     * 获取BGM列表
     */
    const fetchBGMs = async (params = {}) => {
        loading.value = true
        try {
            const response = await bgmService.getBGMs({
                page: pagination.value.page,
                size: pagination.value.size,
                ...params
            })

            bgms.value = response.bgms || []
            pagination.value = {
                page: response.page,
                size: response.size,
                total: response.total,
                total_pages: response.total_pages
            }

            return response
        } catch (error) {
            console.error('获取BGM列表失败:', error)
            ElMessage.error('获取BGM列表失败')
            throw error
        } finally {
            loading.value = false
        }
    }

    /**
     * 获取单个BGM详情
     */
    const getBGM = async (id) => {
        try {
            const response = await bgmService.getBGM(id)
            return response
        } catch (error) {
            console.error('获取BGM详情失败:', error)
            ElMessage.error('获取BGM详情失败')
            throw error
        }
    }

    /**
     * 上传BGM
     */
    const uploadBGM = async (file, name) => {
        try {
            const response = await bgmService.uploadBGM(file, name)
            ElMessage.success('BGM上传成功')
            await fetchBGMs()
            await refreshStats()
            return response
        } catch (error) {
            console.error('BGM上传失败:', error)
            ElMessage.error(error.response?.data?.detail || 'BGM上传失败')
            throw error
        }
    }

    /**
     * 删除BGM
     */
    const deleteBGM = async (id) => {
        try {
            await bgmService.deleteBGM(id)
            ElMessage.success('BGM删除成功')
            await fetchBGMs()
            await refreshStats()
        } catch (error) {
            console.error('BGM删除失败:', error)
            ElMessage.error('BGM删除失败')
            throw error
        }
    }

    /**
     * 刷新统计信息
     */
    const refreshStats = async () => {
        try {
            const response = await bgmService.getBGMStats()
            stats.value = response
        } catch (error) {
            console.error('获取统计信息失败:', error)
        }
    }

    /**
     * 切换页码
     */
    const changePage = (page) => {
        pagination.value.page = page
        fetchBGMs()
    }

    /**
     * 改变每页大小
     */
    const changePageSize = (size) => {
        pagination.value.size = size
        pagination.value.page = 1
        fetchBGMs()
    }

    return {
        // 状态
        bgms,
        loading,
        stats,
        pagination,

        // 计算属性
        hasBGMs,

        // 方法
        fetchBGMs,
        getBGM,
        uploadBGM,
        deleteBGM,
        refreshStats,
        changePage,
        changePageSize
    }
}
