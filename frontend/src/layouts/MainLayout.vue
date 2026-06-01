<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-mark">AI</div>
        <div class="logo-meta">
          <span class="logo-text">Playwright 平台</span>
          <span class="logo-sub">AI Test Automation</span>
        </div>
      </div>

      <nav class="side-nav">
        <p class="nav-group">工作台</p>
        <RouterLink
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          class="nav-item"
          :class="{ active: isActive(item) }"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="side-foot">
        <div class="env-pill">
          <span class="env-dot" />
          引擎在线
        </div>
        <p class="ver">v1.0 · ai-playwright</p>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ name: 'dashboard' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>{{ currentLabel }}</el-breadcrumb-item>
        </el-breadcrumb>

        <div class="topbar-right">
          <el-button
            text
            class="quick-run"
            :icon="VideoPlay"
            @click="$router.push({ name: 'runs' })"
          >
            执行记录
          </el-button>
          <span class="divider" />
          <el-dropdown @command="onCommand">
            <span class="user">
              <span class="avatar">{{ initial }}</span>
              <span class="uname">{{ auth.username }}</span>
              <el-icon class="caret"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>已登录为 {{ auth.username }}</el-dropdown-item>
                <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import { ArrowDown, DataLine, Folder, VideoPlay } from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()

const navItems = [
  { to: '/dashboard', label: '总览仪表盘', icon: DataLine, match: ['dashboard'] },
  {
    to: '/projects',
    label: '项目管理',
    icon: Folder,
    match: ['projects', 'project-detail', 'suite-new', 'suite-edit'],
  },
  { to: '/runs', label: '执行记录', icon: VideoPlay, match: ['runs', 'run-detail'] },
]

function isActive(item) {
  return item.match.includes(route.name)
}

const initial = computed(() => (auth.username || 'U').charAt(0).toUpperCase())

const currentLabel = computed(() => {
  const map = {
    dashboard: '总览仪表盘',
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
  width: 244px;
  background: var(--side-bg);
  border-right: 1px solid var(--side-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 20px 18px;
  border-bottom: 1px solid var(--side-border);
}

.logo-mark {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, var(--brand) 0%, var(--brand-dark) 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  flex-shrink: 0;
}

.logo-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
}

.logo-text {
  font-weight: 650;
  font-size: 14.5px;
  color: var(--side-text-strong);
}

.logo-sub {
  font-size: 11px;
  color: var(--ink-faint);
  letter-spacing: 0.02em;
}

.side-nav {
  flex: 1;
  padding: 14px 12px;
}

.nav-group {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--ink-faint);
  margin: 8px 10px 10px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 11px;
  height: 42px;
  padding: 0 12px;
  border-radius: 9px;
  color: var(--side-text);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 3px;
  transition: background 0.15s, color 0.15s;
}

.nav-item .el-icon {
  font-size: 17px;
}

.nav-item:hover {
  background: var(--side-bg-soft);
  color: var(--side-text-strong);
}

.nav-item.active {
  background: linear-gradient(135deg, var(--brand) 0%, var(--brand-dark) 100%);
  color: #fff;
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35);
}

.side-foot {
  padding: 16px 18px;
  border-top: 1px solid var(--side-border);
}

.env-pill {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: var(--side-text-strong);
  background: var(--side-bg-soft);
  border: 1px solid var(--side-border);
  border-radius: 999px;
  padding: 5px 11px;
}

.env-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.2);
}

.ver {
  margin: 12px 0 0;
  font-size: 11px;
  color: var(--ink-faint);
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: 60px;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.quick-run {
  color: var(--ink-soft);
}

.divider {
  width: 1px;
  height: 22px;
  background: var(--border);
  margin: 0 4px;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--ink);
  font-size: 14px;
  padding: 4px 6px;
  border-radius: 8px;
}

.user:hover {
  background: var(--panel-alt);
}

.avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: linear-gradient(135deg, var(--brand) 0%, var(--brand-dark) 100%);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  font-size: 12px;
}

.uname {
  font-weight: 550;
}

.caret {
  font-size: 13px;
  color: var(--ink-faint);
}

.content {
  flex: 1;
  overflow-y: auto;
  padding: 28px;
}
</style>
