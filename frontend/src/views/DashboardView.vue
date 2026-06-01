<template>
  <div v-loading="loading">
    <div class="page-header">
      <div>
        <h2 class="page-title">总览仪表盘</h2>
        <p class="page-subtitle">测试资产与执行结果的实时概览</p>
      </div>
      <div class="flex gap-12">
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="primary" :icon="VideoPlay" @click="$router.push({ name: 'runs' })">
          运行测试
        </el-button>
      </div>
    </div>

    <!-- Stat cards -->
    <div class="stat-grid">
      <div class="stat-card" v-for="card in cards" :key="card.label">
        <div class="stat-top">
          <span class="stat-label">{{ card.label }}</span>
          <span class="stat-icon" :class="card.tone">
            <el-icon><component :is="card.icon" /></el-icon>
          </span>
        </div>
        <div class="stat-value">{{ card.value }}</div>
        <div class="stat-foot" :class="card.tone">{{ card.foot }}</div>
      </div>
    </div>

    <div class="grid-2">
      <!-- Trend -->
      <div class="panel">
        <div class="flex-between" style="margin-bottom: 18px">
          <h3 class="section-title">近 7 天执行趋势</h3>
          <div class="legend">
            <span class="lg"><i class="sw ok" />通过</span>
            <span class="lg"><i class="sw danger" />失败</span>
          </div>
        </div>
        <div class="chart" v-if="hasTrend">
          <div class="bar-col" v-for="d in stats.trend" :key="d.date">
            <div class="bars">
              <div
                class="bar ok"
                :style="{ height: barH(d.passed) }"
                :title="`通过 ${d.passed}`"
              />
              <div
                class="bar danger"
                :style="{ height: barH(d.failed) }"
                :title="`失败 ${d.failed}`"
              />
            </div>
            <span class="bar-label">{{ d.date }}</span>
          </div>
        </div>
        <div v-else class="empty-mini">暂无执行数据</div>
      </div>

      <!-- Pass rate ring -->
      <div class="panel ring-panel">
        <h3 class="section-title">通过率</h3>
        <div class="ring-wrap">
          <div
            class="ring"
            :style="{
              background: `conic-gradient(var(--ok) ${stats.pass_rate * 3.6}deg, var(--border) 0deg)`,
            }"
          >
            <div class="ring-hole">
              <span class="ring-num">{{ stats.pass_rate }}%</span>
              <span class="ring-cap">通过率</span>
            </div>
          </div>
        </div>
        <div class="ring-stats">
          <div><span class="dot ok" />通过 <b>{{ stats.passed }}</b></div>
          <div><span class="dot danger" />失败 <b>{{ stats.failed }}</b></div>
          <div><span class="dot warn" />进行中 <b>{{ stats.running }}</b></div>
        </div>
      </div>
    </div>

    <!-- Recent runs -->
    <div class="panel-flush" style="margin-top: 18px">
      <div class="flush-head flex-between">
        <h3 class="section-title">最近执行</h3>
        <el-button text type="primary" @click="$router.push({ name: 'runs' })">
          查看全部
        </el-button>
      </div>
      <el-table :data="stats.recent_runs" @row-click="goRun" class="clickable">
        <el-table-column label="#" width="72">
          <template #default="{ row }"><span class="mono">{{ row.id }}</span></template>
        </el-table-column>
        <el-table-column label="类型" width="92">
          <template #default="{ row }">
            <span class="badge" :class="row.kind === 'generate' ? 'warn' : 'info'">
              {{ row.kind === 'generate' ? '生成' : '运行' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="项目" width="150">
          <template #default="{ row }"><span class="mono">{{ row.project_key }}</span></template>
        </el-table-column>
        <el-table-column label="用例集" min-width="160">
          <template #default="{ row }">
            <span class="mono">{{ row.suite_name || '全部' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="环境" width="110">
          <template #default="{ row }"><span class="muted">{{ row.env }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <span class="badge" :class="statusTone(row.status)">
              <span class="dot" />{{ statusText(row.status) }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }"><span class="muted">{{ fmt(row.created_at) }}</span></template>
        </el-table-column>
        <template #empty>
          <div class="empty-mini">还没有执行记录，去运行第一个测试吧</div>
        </template>
      </el-table>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Refresh,
  VideoPlay,
  Folder,
  Files,
  Histogram,
  CircleCheck,
} from '@element-plus/icons-vue'
import api from '../api/client'

const router = useRouter()
const loading = ref(false)
const stats = ref({
  projects: 0,
  suites: 0,
  runs: 0,
  passed: 0,
  failed: 0,
  running: 0,
  pass_rate: 0,
  trend: [],
  recent_runs: [],
})

const cards = computed(() => [
  {
    label: '项目数',
    value: stats.value.projects,
    icon: Folder,
    tone: 'info',
    foot: '配置的测试项目',
  },
  {
    label: '用例集',
    value: stats.value.suites,
    icon: Files,
    tone: 'brand',
    foot: '分层用例集合',
  },
  {
    label: '总执行次数',
    value: stats.value.runs,
    icon: Histogram,
    tone: 'warn',
    foot: `进行中 ${stats.value.running}`,
  },
  {
    label: '通过率',
    value: `${stats.value.pass_rate}%`,
    icon: CircleCheck,
    tone: 'ok',
    foot: `通过 ${stats.value.passed} · 失败 ${stats.value.failed}`,
  },
])

const hasTrend = computed(() =>
  stats.value.trend.some((d) => d.passed > 0 || d.failed > 0)
)

const maxTrend = computed(() => {
  const m = Math.max(1, ...stats.value.trend.map((d) => d.passed + d.failed))
  return m
})

function barH(v) {
  const pct = (v / maxTrend.value) * 100
  return `${Math.max(v > 0 ? 6 : 0, pct)}%`
}

function statusTone(s) {
  return { passed: 'ok', failed: 'danger', running: 'warn', pending: 'neutral' }[s] || 'neutral'
}
function statusText(s) {
  return { passed: '通过', failed: '失败', running: '运行中', pending: '排队中' }[s] || s
}
function fmt(t) {
  return t ? new Date(t).toLocaleString('zh-CN') : '—'
}

function goRun(row) {
  router.push({ name: 'run-detail', params: { runId: row.id } })
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/stats/overview')
    stats.value = data
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.stat-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 16px;
  margin-bottom: 18px;
}

.stat-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.18s, transform 0.18s;
}
.stat-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.stat-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.stat-label {
  font-size: 13px;
  color: var(--ink-soft);
  font-weight: 550;
}

.stat-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 17px;
}
.stat-icon.info {
  background: var(--info-soft);
  color: var(--info);
}
.stat-icon.brand {
  background: var(--brand-soft);
  color: var(--brand);
}
.stat-icon.warn {
  background: var(--warn-soft);
  color: var(--warn);
}
.stat-icon.ok {
  background: var(--ok-soft);
  color: var(--ok);
}

.stat-value {
  font-size: 30px;
  font-weight: 700;
  letter-spacing: -0.03em;
  margin: 14px 0 4px;
}

.stat-foot {
  font-size: 12px;
  color: var(--ink-soft);
}

.grid-2 {
  display: grid;
  grid-template-columns: 1.6fr 1fr;
  gap: 18px;
}
@media (max-width: 920px) {
  .grid-2 {
    grid-template-columns: 1fr;
  }
}

/* Chart */
.legend {
  display: flex;
  gap: 14px;
  font-size: 12px;
  color: var(--ink-soft);
}
.lg {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.sw {
  width: 10px;
  height: 10px;
  border-radius: 3px;
}
.sw.ok {
  background: var(--ok);
}
.sw.danger {
  background: var(--danger);
}

.chart {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
  height: 220px;
  padding-top: 8px;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
  gap: 8px;
}
.bars {
  display: flex;
  align-items: flex-end;
  gap: 4px;
  height: 100%;
  width: 100%;
  justify-content: center;
}
.bar {
  width: 16px;
  border-radius: 5px 5px 0 0;
  min-height: 0;
  transition: height 0.4s ease;
}
.bar.ok {
  background: linear-gradient(180deg, #34d399, var(--ok));
}
.bar.danger {
  background: linear-gradient(180deg, #f87171, var(--danger));
}
.bar-label {
  font-size: 11px;
  color: var(--ink-faint);
}

.empty-mini {
  color: var(--ink-faint);
  font-size: 13px;
  text-align: center;
  padding: 28px 0;
}

/* Ring */
.ring-panel {
  display: flex;
  flex-direction: column;
}
.ring-wrap {
  display: flex;
  justify-content: center;
  padding: 14px 0 18px;
}
.ring {
  width: 156px;
  height: 156px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}
.ring-hole {
  width: 116px;
  height: 116px;
  border-radius: 50%;
  background: var(--panel);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.ring-num {
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.ring-cap {
  font-size: 12px;
  color: var(--ink-soft);
}
.ring-stats {
  display: flex;
  justify-content: space-around;
  border-top: 1px solid var(--border);
  padding-top: 14px;
  font-size: 13px;
  color: var(--ink-soft);
}
.ring-stats b {
  color: var(--ink);
}
.dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  margin-right: 6px;
}
.dot.ok {
  background: var(--ok);
}
.dot.danger {
  background: var(--danger);
}
.dot.warn {
  background: var(--warn);
}

.flush-head {
  padding: 16px 20px;
  border-bottom: 1px solid var(--border);
}
.clickable :deep(.el-table__row) {
  cursor: pointer;
}
</style>
