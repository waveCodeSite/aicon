<template>
  <div class="auth-layout">
    <!-- 背景装饰 -->
    <div class="auth-background">
      <div class="background-pattern"></div>
      <div class="gradient-overlay"></div>
    </div>

    <!-- 主要内容 -->
    <div class="auth-container">
      <!-- Logo和标题 -->
      <div class="auth-header">
        <div class="logo">
          <el-icon class="logo-icon">
            <VideoCamera />
          </el-icon>
          <span class="logo-text">AICG</span>
        </div>
        <h1 class="auth-title">
          <span v-if="title">{{ title }}</span>
          <span v-else>AI内容生成平台</span>
        </h1>
        <p v-if="subtitle" class="auth-subtitle">{{ subtitle }}</p>
      </div>

      <!-- 表单内容 -->
      <div class="auth-content">
        <div class="form-container">
          <router-view v-slot="{ Component, route }">
            <transition name="fade" mode="out-in">
              <component :is="Component" :key="route.path" />
            </transition>
          </router-view>
        </div>
      </div>

      <!-- 底部链接 -->
      <div class="auth-footer">
        <div class="footer-links">
          <a href="#" class="footer-link">使用条款</a>
          <span class="separator">·</span>
          <a href="#" class="footer-link">隐私政策</a>
          <span class="separator">·</span>
          <a href="#" class="footer-link">帮助中心</a>
        </div>
        <div class="copyright">
          © 2024 AICG Platform. All rights reserved.
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { VideoCamera } from '@element-plus/icons-vue'

// Props
defineProps({
  title: {
    type: String,
    default: ''
  },
  subtitle: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.auth-layout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
}

/* 背景样式 */
.auth-background {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 0;
}

.background-pattern {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-image:
    radial-gradient(circle at 25% 25%, rgba(99, 102, 241, 0.1) 0%, transparent 50%),
    radial-gradient(circle at 75% 75%, rgba(168, 85, 247, 0.1) 0%, transparent 50%);
  background-size: 800px 800px;
  animation: float 20s ease-in-out infinite;
}

.gradient-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(135deg,
    rgba(99, 102, 241, 0.02) 0%,
    rgba(168, 85, 247, 0.02) 50%,
    rgba(99, 102, 241, 0.02) 100%);
}

/* 主容器 */
.auth-container {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 400px;
  padding: var(--space-xl);
  display: flex;
  flex-direction: column;
  align-items: center;
}

/* 头部样式 */
.auth-header {
  text-align: center;
  margin-bottom: var(--space-xl);
}

.logo {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-md);
  margin-bottom: var(--space-xl);
}

.logo-icon {
  font-size: 32px;
  color: var(--primary-color);
  padding: var(--space-md);
  background: rgba(99, 102, 241, 0.1);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-lg);
}

.logo-text {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  letter-spacing: 0.5px;
}

.auth-title {
  font-size: var(--text-2xl);
  font-weight: 700;
  color: var(--text-primary);
  margin: 0 0 var(--space-md) 0;
  line-height: 1.2;
}

.auth-subtitle {
  font-size: var(--text-base);
  color: var(--text-secondary);
  margin: 0;
  line-height: 1.5;
}

/* 表单容器 */
.auth-content {
  width: 100%;
  margin-bottom: var(--space-xl);
}

.form-container {
  background: var(--bg-primary);
  border-radius: var(--radius-xl);
  border: 1px solid var(--border-primary);
  box-shadow: var(--shadow-xl);
  padding: var(--space-xl);
  backdrop-filter: blur(10px);
  background: rgba(255, 255, 255, 0.95);
}

/* 底部样式 */
.auth-footer {
  text-align: center;
  width: 100%;
}

.footer-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
  flex-wrap: wrap;
}

.footer-link {
  color: var(--text-secondary);
  text-decoration: none;
  font-size: var(--text-sm);
  transition: color var(--transition-base);
}

.footer-link:hover {
  color: var(--primary-color);
}

.separator {
  color: var(--text-tertiary);
  font-size: var(--text-sm);
}

.copyright {
  color: var(--text-tertiary);
  font-size: var(--text-xs);
  line-height: 1.5;
}

/* 页面切换动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from {
  opacity: 0;
  transform: translateY(20px);
}

.fade-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}

/* 背景动画 */
@keyframes float {
  0%, 100% {
    transform: translate(0, 0) scale(1);
  }
  33% {
    transform: translate(30px, -30px) scale(1.1);
  }
  66% {
    transform: translate(-20px, 20px) scale(0.9);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .auth-container {
    max-width: 100%;
    padding: var(--space-lg);
  }

  .form-container {
    padding: var(--space-lg);
  }

  .logo-icon {
    font-size: 28px;
    padding: var(--space-md);
  }

  .logo-text {
    font-size: var(--text-xl);
  }

  .auth-title {
    font-size: var(--text-xl);
  }

  .footer-links {
    flex-direction: column;
    gap: var(--space-xs);
  }

  .separator {
    display: none;
  }
}

@media (max-width: 480px) {
  .auth-container {
    padding: var(--space-md);
  }

  .form-container {
    padding: var(--space-md);
  }
}

/* 深色主题 */
@media (prefers-color-scheme: dark) {
  .form-container {
    background: rgba(30, 30, 30, 0.95);
    border-color: var(--border-primary);
  }

  .background-pattern {
    background-image:
      radial-gradient(circle at 25% 25%, rgba(99, 102, 241, 0.2) 0%, transparent 50%),
      radial-gradient(circle at 75% 75%, rgba(168, 85, 247, 0.2) 0%, transparent 50%);
  }
}

/* 高对比度模式 */
@media (prefers-contrast: high) {
  .form-container {
    border-width: 2px;
  }

  .background-pattern {
    opacity: 0.3;
  }
}

/* 减少动画偏好 */
@media (prefers-reduced-motion: reduce) {
  .background-pattern {
    animation: none;
  }

  .fade-enter-active,
  .fade-leave-active {
    transition: opacity 0.2s ease;
  }

  .fade-enter-from,
  .fade-leave-to {
    transform: none;
  }
}

/* 无障碍支持 */
.footer-link:focus {
  outline: 2px solid var(--primary-color);
  outline-offset: 2px;
  border-radius: var(--radius-sm);
}
</style>