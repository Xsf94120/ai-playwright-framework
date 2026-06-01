<template>
  <div>
    <div v-if="!scoped" class="page-header">
      <div>
        <p class="kicker">EXECUTIONS</p>
        <h2 class="page-title">执行记录</h2>
        <p class="page-subtitle">触发测试运行、AI 用例生成，并查看实时日志与历史结果</p>
      </div>
      <div class="flex gap-10">
        <el-button :icon="Refresh" @click="loadRuns">刷新</el-button>
        <el-button type="primary" :icon="VideoPlay" @click="runVisible = true">运行测试</el-button>
      </div>
    </div>

    <div v-else class="scoped-head">
      <el-button :icon="Refresh" size="small" @click="loadRuns">刷新</el-button>
    </div>

    <!-- Summary bar -->
    <div class="sum-bar">
      <button class="sum" :class="{ on: filters.status === '' }" @click="setStatus('')">
        <span class="sum-n">{{ counts.all }}</span>
        <span class="sum-l kicker">全部</span>
      </button>
      <button class="sum" :class="{ on: filters.status === 'passed' }" @click="setStatus('passed')">
        <span class="sum-n ok">{{ counts.passed }}</span>
        <span class="sum-l kicker">通过</span>
      </button>
      <button class="sum" :class="{ on: filters.status === 'failed' }" @click="setStatus('failed')">
        <span class="sum-n danger">{{ counts.failed }}</span>
        <span class="sum-l kicker">失败</span>
      </button>
      <button class="sum" :class="{ on: filters.status === 'running' }" @click="setStatus('running')">
        <span class="sum-n warn">{{ counts.running }}</span>
        <span class="sum-l kicker">进行中</span>
      </button>
    </div>

    <!-- Toolbar -->
    <div class="toolbar">
      <div class="searchbox-inline">
        <el-icon><Search /></el-icon>
        <input v-model="filters.q" placeholder="搜索用例集 / 项目 Key…" @keyup.enter="loadRuns" />
      </div>
      <el-select v-model="filters.kind" placeholder="全部类型" clearable style="width: 130px" @change="loadRuns">
        <el-option label="测试运行" value="run" />
        <el-option label="AI 生成" value="generate" />
      </el-select>
      <el-select
        v-if="!scoped"
        v-model="filters.project_id"
        placeholder="全部项目"
        clearable
        style="width: 170px"
        @change="loadRuns"
      >
        <el-option v-for="p in projects" :key="p.id" :label="p.name" :value="p.id" />
      </el-select>
      <span class="toolbar-count mono">{{ runs.length }} 条记录</span>
    </div>

    <div class="panel-flush" v-loading="loading">
      <el-table :data="runs" @row-click="goDetail" class="clickable">
        <el-table-column label="#" width="62">
          <template #default="{ row }"><span class="mono">{{ row.id }}</span></template>
        </el-table-column>
        <el-table-column label="类型" width="78">
          <template #default="{ row }">
            <span class="badge" :class="row.kind === 'generate' ? 'warn' : 'info'">
              {{ row.kind === 'generate' ? 'GEN' : 'RUN' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column v-if="!scoped" label="项目" width="120">
          <template #default="{ row }"><span class="mono proj-key">{{ row.project_key }}</span></template>
        </el-table-column>
        <el-table-column label="用例集" min-width="150">
          <template #default="{ row }"><span class="mono">{{ row.suite_name || '全部' }}</span></template>
        </el-table-column>
        <el-table-column label="环境/浏览器" width="150">
          <template #default="{ row }">
            <span class="muted mono">{{ row.env }} · {{ row.browser }}</span>
          </template>
        </el-table-column>
        <el-table-column label="耗时" width="84">
          <template #default="{ row }"><span class="muted mono">{{ dur(row.duration) }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="108">
          <template #default="{ row }">
            <span class="badge" :class="[statusTone(row.status), row.status === 'running' ? 'live' : '']">
              <span class="dot" />{{ statusText(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="150">
          <template #default="{ row }"><span class="muted">{{ fmt(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column label="" width="64" align="right">
          <template #default="{ row }">
            <el-tooltip content="重跑" placement="top">
              <el-button text circle size="small" :icon="RefreshRight" @click.stop="rerun(row)" />
            </el-tooltip>
          </template>
        </el-table-column>
        <template #empty>
          <div class="empty-mini">
            {{ hasFilters ? '没有符合条件的记录' : '还没有执行记录，点击「运行测试」开始第一次执行' }}
          </div>
        </template>
      </el-table>
    </div>

    <RunDialog
      v-model="runVisible"
      :preset-project-id="scoped ? scopedProjectId : null"
      :lock-project="scoped"
    />
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay, Refresh, RefreshRight, Search } from '@element-plus/icons-vue'
import api from '../api/client'
import RunDialog from '../components/RunDialog.vue'

const route = useRoute()
const router = useRouter()

// 工作区内（/projects/:id/runs）为项目作用域模式
const scopedProjectId = computed(() => route.params.id || null)
const scoped = computed(() => !!scopedProjectId.value)

const runs = ref([])
const projects = ref([])
const loading = ref(false)
const runVisible = ref(false)

const filters = reactive({
  status: '',
  kind: '',
  project_id: route.query.project ? Number(route.query.project) : '',
  q: route.query.q || '',
})

const counts = reactive({ all: 0, passed: 0, failed: 0, running: 0 })

const hasFilters = computed(
  () => filters.status || filters.kind || (!scoped.value && filters.project_id) || filters.q
)

function statusTone(s) {
  return { passed: 'ok', failed: 'danger', running: 'warn', pending: 'neutral' }[s] || 'neutral'
}
function statusText(s) {
  return { passed: '通过', failed: '失败', running: '运行中', pending: '排队中' }[s] || s
}
function fmt(t) {
  return t ? new Date(t).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—'
}
function dur(s) {
  if (s == null) return '—'
  if (s < 60) return `${s.toFixed(s < 10 ? 1 : 0)}s`
  return `${Math.floor(s / 60)}m${Math.round(s % 60)}s`
}

function setStatus(s) {
  filters.status = s
  loadRuns()
}

function buildParams(includeStatus) {
  const params = {}
  if (includeStatus && filters.status) params.status = filters.status
  if (filters.kind) params.kind = filters.kind
  if (scoped.value) params.project_id = scopedProjectId.value
  else if (filters.project_id) params.project_id = filters.project_id
  if (filters.q) params.q = filters.q
  return params
}

async function loadRuns() {
  loading.value = true
  try {
    const { data } = await api.get('/runs', { params: buildParams(true) })
    runs.value = data
    await loadCounts()
  } finally {
    loading.value = false
  }
}

async function loadCounts() {
  const { data } = await api.get('/runs', { params: buildParams(false) })
  counts.all = data.length
  counts.passed = data.filter((r) => r.status === 'passed').length
  counts.failed = data.filter((r) => r.status === 'failed').length
  counts.running = data.filter((r) => ['running', 'pending'].includes(r.status)).length
}

async function loadProjects() {
  if (scoped.value) return
  const { data } = await api.get('/projects')
  projects.value = data
}

function detailRoute(id) {
  return scoped.value
    ? { name: 'project-run-detail', params: { id: scopedProjectId.value, runId: id } }
    : { name: 'run-detail', params: { runId: id } }
}

async function rerun(row) {
  try {
    const { data } = await api.post(`/runs/${row.id}/rerun`)
    ElMessage.success(`已发起重跑 #${data.id}`)
    router.push(detailRoute(data.id))
  } catch {
    /* handled globally */
  }
}

function goDetail(row) {
  router.push(detailRoute(row.id))
}

onMounted(async () => {
  await Promise.all([loadRuns(), loadProjects()])
})
</script>

<style scoped>
.scoped-head {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 12px;
}
.sum-bar {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 14px;
}
.sum {
  background: var(--panel);
  border: none;
  cursor: pointer;
  padding: 14px 16px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  align-items: flex-start;
  transition: background 0.14s;
  position: relative;
}
.sum:hover {
  background: var(--panel-alt);
}
.sum.on {
  background: var(--panel-alt);
}
.sum.on::after {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 2px;
  background: var(--brand);
}
.sum-n {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 24px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1;
}
.sum-n.ok {
  color: var(--ok);
}
.sum-n.danger {
  color: var(--danger);
}
.sum-n.warn {
  color: var(--warn);
}
.sum-l {
  font-size: 10px;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}
.searchbox-inline {
  display: flex;
  align-items: center;
  gap: 8px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0 10px;
  height: 34px;
  width: 260px;
  color: var(--ink-faint);
}
.searchbox-inline:focus-within {
  border-color: var(--brand-border);
  box-shadow: 0 0 0 3px var(--brand-soft);
}
.searchbox-inline input {
  border: none;
  outline: none;
  background: none;
  flex: 1;
  font-size: 13px;
  color: var(--ink);
  font-family: inherit;
  min-width: 0;
}
.toolbar-count {
  margin-left: auto;
  font-size: 12px;
  color: var(--ink-faint);
}

.proj-key {
  color: var(--brand-strong);
  font-weight: 600;
}
.clickable :deep(.el-table__row) {
  cursor: pointer;
}
.empty-mini {
  color: var(--ink-faint);
  font-size: 13px;
  padding: 34px 0;
  text-align: center;
}
</style>
