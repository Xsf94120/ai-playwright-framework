<template>
  <div v-loading="loading" class="workspace">
    <!-- 项目头 -->
    <header class="proj-head">
      <div class="head-left">
        <button class="back-btn" @click="$router.push({ name: 'projects' })">
          <el-icon><Back /></el-icon>
        </button>
        <div class="proj-id">
          <div class="proj-avatar">{{ initial }}</div>
          <div class="proj-meta">
            <div class="proj-name-row">
              <h1 class="proj-name">{{ project.name || '加载中…' }}</h1>
              <span class="proj-key mono">{{ project.key }}</span>
            </div>
            <p class="proj-desc">{{ project.description || '暂无描述' }}</p>
          </div>
        </div>
      </div>
      <div class="head-actions">
        <el-button :icon="MagicStick" @click="goNewSuite">新建用例集</el-button>
        <el-button type="primary" :icon="VideoPlay" @click="runVisible = true">
          运行测试
        </el-button>
      </div>
    </header>

    <!-- 子导航 -->
    <nav class="subnav">
      <RouterLink
        v-for="tab in tabs"
        :key="tab.name"
        :to="{ name: tab.name, params: { id: projectId } }"
        class="subnav-item"
        :class="{ active: isActive(tab) }"
      >
        <el-icon><component :is="tab.icon" /></el-icon>
        <span>{{ tab.label }}</span>
      </RouterLink>
    </nav>

    <!-- 内容 -->
    <div class="workspace-body">
      <router-view v-if="!loading" :project="project" @project-updated="loadProject" />
    </div>

    <RunDialog
      v-model="runVisible"
      :preset-project-id="projectId"
      lock-project
      @submitted="onRunSubmitted"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, provide, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'
import {
  Back,
  VideoPlay,
  MagicStick,
  Odometer,
  Files,
  Histogram,
  Setting,
} from '@element-plus/icons-vue'
import api from '../api/client'
import RunDialog from '../components/RunDialog.vue'

const route = useRoute()
const router = useRouter()
const projectId = computed(() => route.params.id)

const project = ref({})
const loading = ref(true)
const runVisible = ref(false)

const tabs = [
  { name: 'project-overview', label: '概览', icon: Odometer, match: ['project-overview'] },
  {
    name: 'project-suites',
    label: '用例集',
    icon: Files,
    match: ['project-suites', 'suite-new', 'suite-edit'],
  },
  {
    name: 'project-runs',
    label: '执行记录',
    icon: Histogram,
    match: ['project-runs', 'project-run-detail'],
  },
  { name: 'project-settings', label: '设置', icon: Setting, match: ['project-settings'] },
]

const initial = computed(() =>
  (project.value.name || project.value.key || 'P').charAt(0).toUpperCase()
)

function isActive(tab) {
  return tab.match.includes(route.name)
}

async function loadProject() {
  loading.value = true
  try {
    const { data } = await api.get(`/projects/${projectId.value}`)
    project.value = data
  } finally {
    loading.value = false
  }
}

function goNewSuite() {
  router.push({ name: 'suite-new', params: { id: projectId.value } })
}

function onRunSubmitted() {
  /* RunDialog 已自行跳转到运行详情 */
}

// 工作区内的子页面可注入项目数据与刷新方法
provide('workspaceProject', project)
provide('reloadProject', loadProject)

watch(projectId, loadProject)
onMounted(loadProject)
</script>

<style scoped>
.workspace {
  margin: -22px -24px 0;
}

.proj-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  padding: 20px 24px 16px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
}
.head-left {
  display: flex;
  align-items: center;
  gap: 14px;
  min-width: 0;
}
.back-btn {
  width: 34px;
  height: 34px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--panel);
  color: var(--ink-soft);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.14s;
}
.back-btn:hover {
  border-color: var(--border-strong);
  color: var(--ink);
  background: var(--panel-tint);
}
.proj-id {
  display: flex;
  align-items: center;
  gap: 13px;
  min-width: 0;
}
.proj-avatar {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  background: var(--void);
  color: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 19px;
  font-family: 'Space Grotesk', sans-serif;
  flex-shrink: 0;
}
.proj-meta {
  min-width: 0;
}
.proj-name-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.proj-name {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 20px;
  font-weight: 600;
  letter-spacing: -0.01em;
  margin: 0;
  color: var(--ink);
}
.proj-key {
  font-size: 11px;
  color: var(--brand-strong);
  background: var(--brand-soft);
  border: 1px solid var(--brand-border);
  padding: 2px 7px;
  border-radius: 5px;
  font-weight: 600;
}
.proj-desc {
  margin: 3px 0 0;
  font-size: 13px;
  color: var(--ink-faint);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 420px;
}
.head-actions {
  display: flex;
  gap: 10px;
  flex-shrink: 0;
}

.subnav {
  display: flex;
  gap: 2px;
  padding: 0 24px;
  background: var(--panel);
  border-bottom: 1px solid var(--border);
}
.subnav-item {
  display: flex;
  align-items: center;
  gap: 7px;
  padding: 11px 14px;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink-faint);
  text-decoration: none;
  border-bottom: 2px solid transparent;
  margin-bottom: -1px;
  transition: color 0.14s;
}
.subnav-item .el-icon {
  font-size: 15px;
}
.subnav-item:hover {
  color: var(--ink);
}
.subnav-item.active {
  color: var(--brand-strong);
  border-bottom-color: var(--brand);
}

.workspace-body {
  padding: 22px 24px 32px;
}
</style>
