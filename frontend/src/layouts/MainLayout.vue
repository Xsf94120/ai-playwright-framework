<template>
  <div class="layout">
    <aside class="sidebar">
      <div class="logo">
        <div class="logo-mark">
          <span class="logo-glyph">{{ '>' }}_</span>
        </div>
        <div class="logo-meta">
          <span class="logo-text">PLAYWRIGHT</span>
          <span class="logo-sub">AI Test Console</span>
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
          <span class="nav-label">{{ item.label }}</span>
          <span class="nav-key">{{ item.key }}</span>
        </RouterLink>

        <p class="nav-group">快捷操作</p>
        <button class="nav-item action" @click="$router.push({ name: 'projects' })">
          <el-icon><Plus /></el-icon>
          <span class="nav-label">新建项目</span>
        </button>
        <button class="nav-item action" @click="$router.push({ name: 'runs' })">
          <el-icon><VideoPlay /></el-icon>
          <span class="nav-label">运行测试</span>
        </button>
      </nav>

      <div class="side-foot">
        <div class="health" :class="{ down: !online }">
          <span class="health-dot" />
          <div class="health-meta">
            <span class="health-title">{{ online ? '引擎在线' : '引擎离线' }}</span>
            <span class="health-sub mono">{{ online ? 'engine · ready' : 'reconnecting…' }}</span>
          </div>
        </div>
        <p class="ver mono">v1.0 · ai-playwright</p>
      </div>
    </aside>

    <div class="main">
      <header class="topbar">
        <div class="crumbs">
          <span class="crumb-root mono">~/</span>
          <span class="crumb-sep">/</span>
          <span class="crumb-cur">{{ currentLabel }}</span>
        </div>

        <div class="topbar-right">
          <div class="searchbox">
            <el-icon><Search /></el-icon>
            <input
              v-model="search"
              placeholder="搜索运行 / 项目…"
              @keyup.enter="doSearch"
            />
            <span class="search-kbd mono">↵</span>
          </div>
          <span class="divider" />
          <el-dropdown @command="onCommand" trigger="click">
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
import { computed, onMounted, onBeforeUnmount, ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  ArrowDown,
  DataLine,
  Folder,
  VideoPlay,
  Search,
  Plus,
} from '@element-plus/icons-vue'
import { useAuthStore } from '../stores/auth'
import api from '../api/client'

const auth = useAuthStore()
const route = useRoute()
const router = useRouter()
const search = ref('')
const online = ref(true)
let timer = null

const navItems = [
  { to: '/dashboard', label: '总览仪表盘', icon: DataLine, key: 'D', match: ['dashboard'] },
  {
    to: '/projects',
    label: '项目管理',
    icon: Folder,
    key: 'P',
    match: ['projects', 'project-detail', 'suite-new', 'suite-edit'],
  },
  { to: '/runs', label: '执行记录', icon: VideoPlay, key: 'R', match: ['runs', 'run-detail'] },
]

function isActive(item) {
  return item.match.includes(route.name)
}

function doSearch() {
  const q = search.value.trim()
  router.push({ name: 'runs', query: q ? { q } : {} })
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

async function ping() {
  try {
    await api.get('/health', { timeout: 4000 })
    online.value = true
  } catch {
    online.value = false
  }
}

onMounted(() => {
  ping()
  timer = setInterval(ping, 15000)
})
onBeforeUnmount(() => timer && clearInterval(timer))
</script>

<style scoped>
.layout {
  display: flex;
  height: 100%;
}

.sidebar {
  width: 232px;
  background: var(--void);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 11px;
  padding: 17px 16px;
  border-bottom: 1px solid var(--void-border);
}

.logo-mark {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  background: var(--brand);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px -2px rgba(232, 89, 12, 0.5);
}
.logo-glyph {
  font-family: 'JetBrains Mono', monospace;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: -1px;
}

.logo-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}
.logo-text {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 14px;
  letter-spacing: 0.12em;
  color: var(--void-text-strong);
}
.logo-sub {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: var(--ink-faint);
  letter-spacing: 0.04em;
}

.side-nav {
  flex: 1;
  padding: 14px 12px;
}

.nav-group {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.14em;
  color: #6d645a;
  margin: 14px 10px 8px;
}
.nav-group:first-child {
  margin-top: 2px;
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 11px;
  height: 38px;
  padding: 0 11px;
  border-radius: 7px;
  color: var(--void-text);
  text-decoration: none;
  font-size: 13.5px;
  font-weight: 500;
  margin-bottom: 2px;
  transition: background 0.14s, color 0.14s;
  width: 100%;
  background: none;
  border: none;
  cursor: pointer;
  font-family: inherit;
  text-align: left;
  position: relative;
}
.nav-item .el-icon {
  font-size: 16px;
  flex-shrink: 0;
}
.nav-label {
  flex: 1;
}
.nav-key {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  color: #6d645a;
  border: 1px solid var(--void-border);
  border-radius: 4px;
  padding: 1px 5px;
  line-height: 1.4;
}
.nav-item:hover {
  background: var(--void-soft);
  color: var(--void-text-strong);
}
.nav-item.active {
  background: var(--void-soft);
  color: #fff;
}
.nav-item.active::before {
  content: '';
  position: absolute;
  left: -12px;
  top: 8px;
  bottom: 8px;
  width: 3px;
  background: var(--brand);
  border-radius: 0 3px 3px 0;
}
.nav-item.active .el-icon {
  color: var(--brand);
}
.nav-item.action {
  color: var(--ink-faint);
  font-size: 13px;
}

.side-foot {
  padding: 14px 16px;
  border-top: 1px solid var(--void-border);
}
.health {
  display: flex;
  align-items: center;
  gap: 9px;
}
.health-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ok);
  box-shadow: 0 0 0 3px rgba(47, 158, 68, 0.18);
  flex-shrink: 0;
}
.health.down .health-dot {
  background: var(--danger);
  box-shadow: 0 0 0 3px rgba(224, 49, 49, 0.18);
}
.health-meta {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}
.health-title {
  font-size: 12.5px;
  color: var(--void-text-strong);
  font-weight: 550;
}
.health-sub {
  font-size: 10px;
  color: var(--ink-faint);
}
.ver {
  margin: 12px 0 0;
  font-size: 10px;
  color: #57504780;
  color: #5a534a;
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.topbar {
  height: 56px;
  background: rgba(244, 242, 237, 0.8);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 22px;
  position: sticky;
  top: 0;
  z-index: 10;
}

.crumbs {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13.5px;
}
.crumb-root {
  color: var(--ink-faint);
  font-size: 12px;
}
.crumb-sep {
  color: var(--ink-faint);
}
.crumb-cur {
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 600;
  color: var(--ink);
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 10px;
}

.searchbox {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 7px;
  padding: 0 10px;
  height: 34px;
  width: 240px;
  color: var(--ink-faint);
  transition: border-color 0.15s, box-shadow 0.15s;
}
.searchbox:focus-within {
  border-color: var(--brand-border);
  box-shadow: 0 0 0 3px var(--brand-soft);
}
.searchbox input {
  border: none;
  outline: none;
  background: none;
  flex: 1;
  font-size: 13px;
  color: var(--ink);
  font-family: inherit;
  min-width: 0;
}
.search-kbd {
  font-size: 11px;
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 0 5px;
  color: var(--ink-faint);
}

.divider {
  width: 1px;
  height: 20px;
  background: var(--border);
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--ink);
  font-size: 13.5px;
  padding: 4px 6px;
  border-radius: 7px;
}
.user:hover {
  background: var(--panel-tint);
}
.avatar {
  width: 27px;
  height: 27px;
  border-radius: 7px;
  background: var(--void);
  color: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 12px;
  font-family: 'Space Grotesk', sans-serif;
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
  padding: 22px 24px 32px;
}
@media (max-width: 720px) {
  .searchbox {
    width: 140px;
  }
}
</style>
