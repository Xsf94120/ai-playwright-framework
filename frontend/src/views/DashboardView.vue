<template>
  <div v-loading="loading">
    <div class="page-header">
      <div>
        <p class="kicker">OVERVIEW</p>
        <h2 class="page-title">总览仪表盘</h2>
        <p class="page-subtitle">测试资产与执行结果的实时概览</p>
      </div>
      <div class="flex gap-10">
        <el-button :icon="Refresh" @click="load">刷新</el-button>
        <el-button type="primary" :icon="VideoPlay" @click="$router.push({ name: 'runs' })">
          运行测试
        </el-button>
      </div>
    </div>

    <!-- KPI strip -->
    <div class="kpi-strip">
      <div class="kpi" v-for="(card, i) in cards" :key="card.label" :class="{ tall: i === 0 }">
        <div class="kpi-head">
          <span class="kpi-label kicker">{{ card.label }}</span>
          <el-icon class="kpi-ic" :class="card.tone"><component :is="card.icon" /></el-icon>
        </div>
        <div class="kpi-value">{{ card.value }}</div>
        <div class="kpi-foot">
          <span class="kpi-foot-dot" :class="card.tone" />{{ card.foot }}
        </div>
      </div>
    </div>

    <div class="grid-main">
      <!-- Trend -->
      <div class="panel-flush">
        <div class="panel-head">
          <h3 class="section-title tick">近 7 天执行趋势</h3>
          <div class="legend">
            <span class="lg"><i class="sw ok" />通过</span>
            <span class="lg"><i class="sw danger" />失败</span>
          </div>
        </div>
        <div class="panel-body">
          <div class="chart" v-if="hasTrend">
            <div class="bar-col" v-for="d in stats.trend" :key="d.date">
              <span class="bar-total mono">{{ d.passed + d.failed || '' }}</span>
              <div class="bars">
                <div class="bar ok" :style="{ height: barH(d.passed) }" :title="`通过 ${d.passed}`" />
                <div class="bar danger" :style="{ height: barH(d.failed) }" :title="`失败 ${d.failed}`" />
              </div>
              <span class="bar-label mono">{{ d.date }}</span>
            </div>
          </div>
          <div v-else class="empty-mini">暂无执行数据</div>
        </div>
      </div>

      <!-- Pass rate ring -->
      <div class="panel-flush">
        <div class="panel-head">
          <h3 class="section-title tick">总体通过率</h3>
        </div>
        <div class="panel-body ring-body">
          <div
            class="ring"
            :style="{ background: `conic-gradient(var(--ok) ${stats.pass_rate * 3.6}deg, var(--line) 0deg)` }"
          >
            <div class="ring-hole">
              <span class="ring-num">{{ stats.pass_rate }}<small>%</small></span>
              <span class="ring-cap kicker">PASS RATE</span>
            </div>
          </div>
          <div class="ring-stats">
            <div class="rs"><span class="dot ok" /><span class="rs-n">{{ stats.passed }}</span><span class="rs-l">通过</span></div>
            <div class="rs"><span class="dot danger" /><span class="rs-n">{{ stats.failed }}</span><span class="rs-l">失败</span></div>
            <div class="rs"><span class="dot warn" /><span class="rs-n">{{ stats.running }}</span><span class="rs-l">进行中</span></div>
          </div>
        </div>
      </div>
    </div>

    <div class="grid-second">
      <!-- Project breakdown -->
      <div class="panel-flush">
        <div class="panel-head">
          <h3 class="section-title tick">项目维度</h3>
          <el-button text type="primary" size="small" @click="$router.push({ name: 'projects' })">
            管理项目
          </el-button>
        </div>
        <div class="proj-list" v-if="stats.project_breakdown.length">
          <div class="proj-row" v-for="p in stats.project_breakdown" :key="p.id" @click="goProject(p.id)">
            <div class="proj-id">
              <span class="proj-key mono">{{ p.key }}</span>
              <span class="proj-name">{{ p.name }}</span>
            </div>
            <div class="proj-bar">
              <div class="proj-bar-track">
                <div class="proj-bar-fill" :style="{ width: p.pass_rate + '%' }" />
              </div>
              <span class="proj-rate mono">{{ p.pass_rate }}%</span>
            </div>
            <div class="proj-meta mono">
              <span>{{ p.suites }} 用例集</span>
              <span class="proj-dot">·</span>
              <span>{{ p.runs }} 次执行</span>
            </div>
          </div>
        </div>
        <div v-else class="empty-mini">暂无项目</div>
      </div>

      <!-- Top failing -->
      <div class="panel-flush">
        <div class="panel-head">
          <h3 class="section-title tick">高频失败用例</h3>
        </div>
        <div class="fail-list" v-if="stats.top_failing.length">
          <div class="fail-row" v-for="(f, i) in stats.top_failing" :key="i">
            <span class="fail-rank mono">{{ i + 1 }}</span>
            <div class="fail-meta">
              <span class="fail-name mono">{{ f.suite_name }}</span>
              <span class="fail-proj mono">{{ f.project_key }}</span>
            </div>
            <span class="badge danger"><span class="dot" />{{ f.failures }} 次</span>
          </div>
        </div>
        <div v-else class="empty-ok">
          <el-icon><CircleCheck /></el-icon>
          <span>暂无失败用例，状态良好</span>
        </div>
      </div>
    </div>

    <!-- Recent runs -->
    <div class="panel-flush" style="margin-top: 16px">
      <div class="panel-head">
        <h3 class="section-title tick">最近执行</h3>
        <el-button text type="primary" size="small" @click="$router.push({ name: 'runs' })">
          查看全部
        </el-button>
      </div>
      <el-table :data="stats.recent_runs" @row-click="goRun" class="clickable">
        <el-table-column label="#" width="64">
          <template #default="{ row }"><span class="mono">{{ row.id }}</span></template>
        </el-table-column>
        <el-table-column label="类型" width="80">
          <template #default="{ row }">
            <span class="badge" :class="row.kind === 'generate' ? 'warn' : 'info'">
              {{ row.kind === 'generate' ? 'GEN' : 'RUN' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="项目" width="130">
          <template #default="{ row }"><span class="mono">{{ row.project_key }}</span></template>
        </el-table-column>
        <el-table-column label="用例集" min-width="150">
          <template #default="{ row }"><span class="mono">{{ row.suite_name || '全部' }}</span></template>
        </el-table-column>
        <el-table-column label="环境" width="90">
          <template #default="{ row }"><span class="muted mono">{{ row.env }}</span></template>
        </el-table-column>
        <el-table-column label="耗时" width="90">
          <template #default="{ row }"><span class="muted mono">{{ dur(row.duration) }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="108">
          <template #default="{ row }">
            <span class="badge" :class="statusTone(row.status)"><span class="dot" />{{ statusText(row.status) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="160">
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
  Timer,
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
  today_runs: 0,
  avg_duration: 0,
  trend: [],
  project_breakdown: [],
  top_failing: [],
  recent_runs: [],
})

const cards = computed(() => [
  {
    label: '通过率',
    value: `${stats.value.pass_rate}%`,
    icon: CircleCheck,
    tone: 'ok',
    foot: `通过 ${stats.value.passed} · 失败 ${stats.value.failed}`,
  },
  {
    label: '总执行',
    value: stats.value.runs,
    icon: Histogram,
    tone: 'brand',
    foot: `今日 ${stats.value.today_runs} 次`,
  },
  {
    label: '平均耗时',
    value: dur(stats.value.avg_duration),
    icon: Timer,
    tone: 'info',
    foot: '近 100 次执行',
  },
  {
    label: '项目',
    value: stats.value.projects,
    icon: Folder,
    tone: 'neutral',
    foot: `${stats.value.suites} 个用例集`,
  },
])

const hasTrend = computed(() => stats.value.trend.some((d) => d.passed > 0 || d.failed > 0))
const maxTrend = computed(() => Math.max(1, ...stats.value.trend.map((d) => d.passed + d.failed)))

function barH(v) {
  const pct = (v / maxTrend.value) * 100
  return `${Math.max(v > 0 ? 8 : 0, pct)}%`
}
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
  const m = Math.floor(s / 60)
  return `${m}m${Math.round(s % 60)}s`
}
function goRun(row) {
  router.push({ name: 'run-detail', params: { runId: row.id } })
}
function goProject(id) {
  router.push({ name: 'project-detail', params: { id } })
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
/* KPI strip */
.kpi-strip {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 16px;
}
@media (max-width: 880px) {
  .kpi-strip {
    grid-template-columns: repeat(2, 1fr);
  }
}
.kpi {
  background: var(--panel);
  padding: 16px 18px;
  transition: background 0.15s;
}
.kpi:hover {
  background: var(--panel-alt);
}
.kpi-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.kpi-ic {
  font-size: 15px;
  color: var(--ink-faint);
}
.kpi-ic.ok {
  color: var(--ok);
}
.kpi-ic.brand {
  color: var(--brand);
}
.kpi-ic.info {
  color: var(--info);
}
.kpi-value {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 30px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin: 10px 0 6px;
  line-height: 1;
}
.kpi-foot {
  font-size: 11.5px;
  color: var(--ink-soft);
  display: flex;
  align-items: center;
  gap: 6px;
}
.kpi-foot-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--ink-faint);
}
.kpi-foot-dot.ok {
  background: var(--ok);
}
.kpi-foot-dot.brand {
  background: var(--brand);
}
.kpi-foot-dot.info {
  background: var(--info);
}

/* Main grid */
.grid-main {
  display: grid;
  grid-template-columns: 1.7fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
}
.grid-second {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}
@media (max-width: 880px) {
  .grid-main,
  .grid-second {
    grid-template-columns: 1fr;
  }
}

.panel-body {
  padding: 18px;
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
  width: 9px;
  height: 9px;
  border-radius: 2px;
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
  gap: 10px;
  height: 196px;
}
.bar-col {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  justify-content: flex-end;
  gap: 7px;
}
.bar-total {
  font-size: 11px;
  color: var(--ink-faint);
  height: 14px;
}
.bars {
  display: flex;
  align-items: flex-end;
  gap: 3px;
  height: 100%;
  width: 100%;
  justify-content: center;
}
.bar {
  width: 14px;
  border-radius: 3px 3px 0 0;
  transition: height 0.4s ease;
}
.bar.ok {
  background: var(--ok);
}
.bar.danger {
  background: var(--danger);
}
.bar-label {
  font-size: 10.5px;
  color: var(--ink-faint);
}

/* Ring */
.ring-body {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16px;
}
.ring {
  width: 150px;
  height: 150px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 6px;
}
.ring-hole {
  width: 112px;
  height: 112px;
  border-radius: 50%;
  background: var(--panel);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 3px;
}
.ring-num {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 32px;
  font-weight: 600;
  letter-spacing: -0.02em;
  line-height: 1;
}
.ring-num small {
  font-size: 15px;
  color: var(--ink-soft);
}
.ring-cap {
  font-size: 9.5px;
}
.ring-stats {
  display: flex;
  width: 100%;
  border-top: 1px solid var(--line);
  padding-top: 14px;
}
.rs {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
}
.rs-n {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 17px;
  font-weight: 600;
}
.rs-l {
  font-size: 11px;
  color: var(--ink-soft);
}
.dot {
  display: inline-block;
  width: 7px;
  height: 7px;
  border-radius: 50%;
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

/* Project breakdown */
.proj-list {
  padding: 6px 0;
}
.proj-row {
  display: grid;
  grid-template-columns: 1.2fr 1.4fr auto;
  align-items: center;
  gap: 14px;
  padding: 11px 16px;
  cursor: pointer;
  border-bottom: 1px solid var(--line);
  transition: background 0.14s;
}
.proj-row:last-child {
  border-bottom: none;
}
.proj-row:hover {
  background: var(--panel-tint);
}
.proj-id {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.proj-key {
  color: var(--brand-strong);
  font-weight: 600;
  font-size: 12px;
}
.proj-name {
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.proj-bar {
  display: flex;
  align-items: center;
  gap: 9px;
}
.proj-bar-track {
  flex: 1;
  height: 6px;
  background: var(--line);
  border-radius: 3px;
  overflow: hidden;
}
.proj-bar-fill {
  height: 100%;
  background: var(--ok);
  border-radius: 3px;
  transition: width 0.5s ease;
}
.proj-rate {
  font-size: 12px;
  color: var(--ink-soft);
  width: 38px;
  text-align: right;
}
.proj-meta {
  font-size: 11px;
  color: var(--ink-faint);
  white-space: nowrap;
}
.proj-dot {
  margin: 0 4px;
}

/* Fail list */
.fail-list {
  padding: 6px 0;
}
.fail-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 11px 16px;
  border-bottom: 1px solid var(--line);
}
.fail-row:last-child {
  border-bottom: none;
}
.fail-rank {
  width: 20px;
  height: 20px;
  border-radius: 5px;
  background: var(--panel-tint);
  border: 1px solid var(--border);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--ink-soft);
  flex-shrink: 0;
}
.fail-meta {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
}
.fail-name {
  font-size: 13px;
  font-weight: 550;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.fail-proj {
  font-size: 11px;
  color: var(--ink-faint);
}
.empty-ok {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  padding: 36px 0;
  color: var(--ok);
  font-size: 13px;
}
.empty-ok .el-icon {
  font-size: 26px;
}

.empty-mini {
  color: var(--ink-faint);
  font-size: 13px;
  text-align: center;
  padding: 30px 0;
}
.clickable :deep(.el-table__row) {
  cursor: pointer;
}
</style>
