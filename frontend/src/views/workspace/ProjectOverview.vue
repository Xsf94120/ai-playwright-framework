<template>
  <div v-loading="loading" class="overview">
    <!-- 配置就绪引导（环境/模型未配齐时显示） -->
    <div v-if="setupTasks.length" class="setup-card">
      <div class="setup-head">
        <el-icon class="setup-icon"><Compass /></el-icon>
        <div>
          <h3>完成配置即可开始测试</h3>
          <p>以下步骤建议在首次运行前完成</p>
        </div>
      </div>
      <ul class="setup-list">
        <li v-for="t in setupTasks" :key="t.key">
          <el-icon class="todo-dot"><CircleCheck v-if="t.done" /><Warning v-else /></el-icon>
          <span :class="{ done: t.done }">{{ t.label }}</span>
          <el-button v-if="!t.done" link type="primary" @click="t.action">{{ t.cta }}</el-button>
        </li>
      </ul>
    </div>

    <!-- 指标卡 -->
    <div class="stat-grid">
      <div class="stat">
        <span class="stat-label kicker">用例集</span>
        <span class="stat-value">{{ suites.length }}</span>
        <span class="stat-foot">个分层用例集</span>
      </div>
      <div class="stat">
        <span class="stat-label kicker">总执行</span>
        <span class="stat-value">{{ stats.total }}</span>
        <span class="stat-foot">次运行记录</span>
      </div>
      <div class="stat">
        <span class="stat-label kicker">通过率</span>
        <span class="stat-value" :class="passTone">{{ stats.passRate }}%</span>
        <span class="stat-foot">{{ stats.passed }}/{{ stats.finished }} 通过</span>
      </div>
      <div class="stat">
        <span class="stat-label kicker">平均耗时</span>
        <span class="stat-value">{{ stats.avgDuration }}</span>
        <span class="stat-foot">每次运行</span>
      </div>
    </div>

    <div class="two-col">
      <!-- 最近执行 -->
      <section class="panel-flush">
        <div class="sec-head">
          <h3 class="sec-title">最近执行</h3>
          <el-button link type="primary" @click="goRuns">查看全部</el-button>
        </div>
        <el-table :data="recentRuns" @row-click="goRunDetail" class="clickable" :show-header="false">
          <el-table-column width="50">
            <template #default="{ row }">
              <span class="badge" :class="row.kind === 'generate' ? 'warn' : 'info'">
                {{ row.kind === 'generate' ? 'G' : 'R' }}
              </span>
            </template>
          </el-table-column>
          <el-table-column>
            <template #default="{ row }">
              <span class="mono run-suite">{{ row.suite_name || '全部用例集' }}</span>
              <span class="muted run-env mono">{{ row.env }} · {{ row.browser }}</span>
            </template>
          </el-table-column>
          <el-table-column width="90" align="right">
            <template #default="{ row }">
              <span class="muted mono dur">{{ dur(row.duration) }}</span>
            </template>
          </el-table-column>
          <el-table-column width="96" align="right">
            <template #default="{ row }">
              <span class="badge" :class="statusTone(row.status)">
                <span class="dot" />{{ statusText(row.status) }}
              </span>
            </template>
          </el-table-column>
          <template #empty>
            <div class="empty-mini">还没有执行记录</div>
          </template>
        </el-table>
      </section>

      <!-- 环境状态 -->
      <section class="panel">
        <div class="sec-head">
          <h3 class="sec-title">环境</h3>
          <el-button link type="primary" @click="goSettings">管理</el-button>
        </div>
        <ul class="env-list">
          <li v-for="e in environments" :key="e.name" class="env-item">
            <span class="env-dot" :class="{ ready: hasUrl(e) }" />
            <span class="env-name mono">{{ e.name }}</span>
            <span class="env-url mono" :class="{ missing: !hasUrl(e) }">
              {{ hasUrl(e) ? e.base_url : '未配置 URL' }}
            </span>
          </li>
          <li v-if="!environments.length" class="empty-mini">尚未配置环境</li>
        </ul>
        <div class="model-row">
          <span class="env-dot" :class="{ ready: llmReady }" />
          <span class="env-name">模型 (LLM)</span>
          <span class="env-url mono" :class="{ missing: !llmReady }">
            {{ llmReady ? llm.model || '已配置' : '未配置' }}
          </span>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { computed, inject, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { Compass, CircleCheck, Warning } from '@element-plus/icons-vue'
import api from '../../api/client'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id
const workspaceProject = inject('workspaceProject', ref({}))

const loading = ref(false)
const suites = ref([])
const runs = ref([])
const llm = ref({})
const llmReady = ref(false)

const environments = computed(() => workspaceProject.value?.environments || [])
const stats = reactive({
  total: 0,
  finished: 0,
  passed: 0,
  passRate: 0,
  avgDuration: '—',
})

const recentRuns = computed(() => runs.value.slice(0, 6))
const passTone = computed(() =>
  stats.passRate >= 80 ? 'ok' : stats.passRate >= 50 ? 'warn' : 'danger'
)

function hasUrl(e) {
  return !!(e.base_url || '').trim()
}

const setupTasks = computed(() => {
  const envReady = environments.value.some(hasUrl)
  const tasks = [
    {
      key: 'env',
      label: '配置至少一个环境的 BASE_URL',
      done: envReady,
      cta: '去配置',
      action: goSettings,
    },
    {
      key: 'llm',
      label: '配置驱动 AI 的大模型接口',
      done: llmReady.value,
      cta: '去配置',
      action: goSettings,
    },
    {
      key: 'suite',
      label: '创建第一个用例集',
      done: suites.value.length > 0,
      cta: '新建',
      action: goNewSuite,
    },
  ]
  // 全部完成则不显示引导
  return tasks.every((t) => t.done) ? [] : tasks
})

function statusTone(s) {
  return { passed: 'ok', failed: 'danger', running: 'warn', pending: 'neutral' }[s] || 'neutral'
}
function statusText(s) {
  return { passed: '通过', failed: '失败', running: '运行中', pending: '排队中' }[s] || s
}
function dur(s) {
  if (s == null) return '—'
  if (s < 60) return `${s.toFixed(s < 10 ? 1 : 0)}s`
  return `${Math.floor(s / 60)}m${Math.round(s % 60)}s`
}

function goRuns() {
  router.push({ name: 'project-runs', params: { id: projectId } })
}
function goRunDetail(row) {
  router.push({ name: 'project-run-detail', params: { id: projectId, runId: row.id } })
}
function goSettings() {
  router.push({ name: 'project-settings', params: { id: projectId } })
}
function goNewSuite() {
  router.push({ name: 'suite-new', params: { id: projectId } })
}

function computeStats() {
  const list = runs.value
  stats.total = list.length
  const finished = list.filter((r) => ['passed', 'failed'].includes(r.status))
  stats.finished = finished.length
  stats.passed = finished.filter((r) => r.status === 'passed').length
  stats.passRate = finished.length
    ? Math.round((stats.passed / finished.length) * 100)
    : 0
  const durs = list.map((r) => r.duration).filter((d) => d != null)
  if (durs.length) {
    const avg = durs.reduce((a, b) => a + b, 0) / durs.length
    stats.avgDuration = dur(avg)
  } else {
    stats.avgDuration = '—'
  }
}

onMounted(async () => {
  loading.value = true
  try {
    const [suiteRes, runRes, llmRes] = await Promise.all([
      api.get(`/projects/${projectId}/suites`),
      api.get('/runs', { params: { project_id: projectId } }),
      api.get(`/projects/${projectId}/llm`),
    ])
    suites.value = suiteRes.data
    runs.value = runRes.data
    llm.value = llmRes.data
    llmReady.value = !!(llmRes.data.api_key_set && llmRes.data.base_url)
    computeStats()
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.overview {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.setup-card {
  background: var(--panel);
  border: 1px solid var(--brand-border);
  border-radius: var(--radius);
  padding: 18px 20px;
}
.setup-head {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 14px;
}
.setup-icon {
  font-size: 22px;
  color: var(--brand);
}
.setup-head h3 {
  margin: 0;
  font-size: 15px;
  font-family: 'Space Grotesk', sans-serif;
}
.setup-head p {
  margin: 2px 0 0;
  font-size: 12.5px;
  color: var(--ink-faint);
}
.setup-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 9px;
}
.setup-list li {
  display: flex;
  align-items: center;
  gap: 9px;
  font-size: 13.5px;
}
.todo-dot {
  font-size: 16px;
  color: var(--warn);
}
.setup-list .done {
  color: var(--ink-faint);
  text-decoration: line-through;
}
.setup-list li:has(.done) .todo-dot {
  color: var(--ok);
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
}
.stat {
  background: var(--panel);
  padding: 16px 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.stat-label {
  font-size: 10px;
}
.stat-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 28px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1;
  color: var(--ink);
}
.stat-value.ok {
  color: var(--ok);
}
.stat-value.warn {
  color: var(--warn);
}
.stat-value.danger {
  color: var(--danger);
}
.stat-foot {
  font-size: 11.5px;
  color: var(--ink-faint);
}

.two-col {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
}
@media (max-width: 900px) {
  .two-col,
  .stat-grid {
    grid-template-columns: 1fr 1fr;
  }
}

.sec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
  padding: 0 2px;
}
.panel .sec-head {
  margin-bottom: 12px;
}
.sec-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 14px;
  font-weight: 600;
  margin: 0;
}

.clickable :deep(.el-table__row) {
  cursor: pointer;
}
.run-suite {
  font-weight: 500;
}
.run-env {
  display: block;
  font-size: 11px;
  color: var(--ink-faint);
  margin-top: 2px;
}
.dur {
  font-size: 12px;
}
.empty-mini {
  color: var(--ink-faint);
  font-size: 13px;
  padding: 24px 0;
  text-align: center;
}

.env-list {
  list-style: none;
  margin: 0 0 12px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.env-item,
.model-row {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
}
.model-row {
  padding-top: 12px;
  border-top: 1px solid var(--border);
}
.env-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ink-faint);
  flex-shrink: 0;
}
.env-dot.ready {
  background: var(--ok);
  box-shadow: 0 0 0 3px rgba(47, 158, 68, 0.16);
}
.env-name {
  font-weight: 600;
  color: var(--ink);
  min-width: 64px;
}
.env-url {
  font-size: 12px;
  color: var(--ink-soft);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.env-url.missing {
  color: var(--danger);
}
</style>
