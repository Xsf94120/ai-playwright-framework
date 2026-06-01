<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-mark">AI</div>
        <span class="logo-text">Playwright 平台</span>
      </div>
      <el-menu :default-active="activeMenu" router class="side-menu">
        <el-menu-item index="/projects">
          <el-icon><Folder /></el-icon>
          <span>项目管理</span>
        </el-menu-item>
        <el-menu-item index="/runs">
          <el-icon><VideoPlay /></el-icon>
          <span>执行记录</span>
        </el-menu-item>
      </el-menu>
    </aside>

    <div class="main">
      <header class="topbar">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ name: 'projects' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>{{ currentLabel }}</el-breadcrumb-item>
        </el-breadcrumb>
        <el-dropdown @command="onCommand">
          <span class="user">
            <el-icon><UserFilled /></el-icon>
            {{ auth.username }}
            <el-icon><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const activeMenu = computed(() => {
  if (route.path.startsWith('/runs')) return '/runs'
  return '/projects'
})

const currentLabel = computed(() => {
  const map = {
    projects: '项目管理',
    'project-detail': '项目详情',
    'suite-new': '新建用例集',
    'suite-edit': '编辑用例集',
    runs: '执行记录',
    'run-detail': '运行详情',
  }
  return map[route.name] || ''
})

function onCommand(command) {
  if (command === 'logout') {
    auth.logout()
    router.replace({ name: 'login' })
  }
}
</script>

<style scoped>
.layout {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 224px;
  background: #14322f;
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 18px;
  color: #fff;
}

.logo-mark {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
}

.logo-text {
  font-weight: 600;
  font-size: 15px;
}

.side-menu {
  border-right: none;
  background: transparent;
  padding: 6px 10px;
}

.side-menu :deep(.el-menu-item) {
  color: #b9d3cf;
  border-radius: 8px;
  margin-bottom: 4px;
  height: 46px;
}

.side-menu :deep(.el-menu-item.is-active) {
  background: var(--brand);
  color: #fff;
}

.side-menu :deep(.el-menu-item:hover) {
  background: rgba(47, 111, 106, 0.4);
  color: #fff;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: 58px;
  background: #fff;
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
}

.user {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  color: var(--ink);
  font-size: 14px;
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}
</style>
