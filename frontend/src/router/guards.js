import { useAuthStore } from '@/stores/auth'

export function setupAuthGuard(router) {
  // 全局前置守卫
  router.beforeEach(async (to, from, next) => {
    const authStore = useAuthStore()

    // 如果用户已登录但还没有获取用户信息，先获取
    if (authStore.isAuthenticated && !authStore.user) {
      try {
        await authStore.getCurrentUser()
      } catch (error) {
        console.error('获取用户信息失败:', error)
        authStore.logout()
        next({ name: 'Login', query: { redirect: to.fullPath } })
        return
      }
    }

    // 检查是否需要认证
    if (to.meta.requiresAuth && !authStore.isAuthenticated) {
      next({ name: 'Login', query: { redirect: to.fullPath } })
      return
    }

    // 检查是否需要游客状态（已登录用户不能访问登录/注册页面）
    if (to.meta.requiresGuest && authStore.isAuthenticated) {
      next({ name: 'Dashboard' })
      return
    }

    // 检查邮箱验证
    if (to.meta.requiresVerified && authStore.user && !authStore.user.is_verified) {
      next({ name: 'Profile' })
      return
    }

    // 检查管理员权限
    if (to.meta.requiresAdmin && authStore.user && !authStore.user.is_admin) {
      next({ name: 'Dashboard' })
      return
    }

    next()
  })

  // 全局后置钩子
  router.afterEach((to, from) => {
    // 可以在这里添加页面访问日志、统计等
    document.title = `${to.meta.title || 'AICG Platform'} - Content Distribution Platform`
  })
}

// 权限检查函数
export function hasPermission(user, permission) {
  if (!user) return false

  // 这里可以根据实际的权限系统进行扩展
  switch (permission) {
    case 'admin':
      return user.is_admin || false
    case 'verified':
      return user.is_verified || false
    case 'active':
      return user.is_active || false
    default:
      return true
  }
}

// 角色检查函数
export function hasRole(user, role) {
  if (!user) return false

  // 这里可以根据实际的角色系统进行扩展
  return user.role === role
}