<template>
  <div v-loading="loading">
    <div class="page-header">
      <div>
        <p class="kicker">RUN #{{ run.id }}</p>
        <h2 class="page-title">
          {{ run.suite_name || '全部用例' }}
          <span class="badge" :class="[statusTone(run.status), run.status === 'running' ? 'live' : '']">
            <span class="dot" />{{ statusText(run.status) }}
          </span>
          <span class="badge" :class="run.kind === 'generate' ? 'warn' : 'info'">
            {{ run.kind === 'generate' ? 'AI 生成' : '测试运行' }}
          </span>
        </h2>
        <p class="page-subtitle mono cmd">$ {{ run.command || '准备中…' }}</p>
      </div>
      <div class="flex gap-10">
        <el-button :icon="RefreshRight" @click="doRerun" :disabled="run.status === 'running'">重跑</el-button>
        <el-button :icon="Back" @click="goBack">返回</el-button>
      </div>
    </div>

    <!-- Result summary -->
    <div class="meta-grid">
      <div class="meta-item">
        <span class="meta-label kicker">项目</span>
        <span class="meta-val mono key">{{ run.project_key }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label kicker">环境</span>
        <span class="meta-val mono">{{ run.env }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label kicker">浏览器</span>
        <span class="meta-val mono">{{ run.browser }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label kicker">AI 模式</span>
        <span class="meta-val mono">{{ run.ai_mode }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label kicker">耗时</span>
        <span class="meta-val mono">{{ dur(run.duration) }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label kicker">退出码</span>
        <span class="meta-val mono" :class="exitTone">{{ run.exit_code ?? '—' }}</span>
      </div>
    </div>

    <!-- Log console -->
    <div class="panel-flush">
      <div class="panel-head log-head">
        <div class="log-title">
          <el-icon><Monitor /></el-icon>
          <span>实时日志</span>
          <span v-if="connected" class="live-tag mono">● LIVE</span>
          <span class="line-count mono">{{ filteredLines.length }} 行</span>
        </div>
        <div class="log-tools">
          <div class="log-search">
            <el-icon><Search /></el-icon>
            <input v-model="logQuery" placeholder="过滤日志…" />
          </div>
          <el-tooltip content="自动滚动" placement="top">
            <button class="tool-btn" :class="{ on: autoScroll }" @click="autoScroll = !autoScroll">
              <el-icon><Bottom /></el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="复制全部" placement="top">
            <button class="tool-btn" @click="copyLog"><el-icon><CopyDocument /></el-icon></button>
          </el-tooltip>
          <el-tooltip content="下载日志" placement="top">
            <button class="tool-btn" @click="downloadLog"><el-icon><Download /></el-icon></button>
          </el-tooltip>
        </div>
      </div>
      <div ref="consoleRef" class="log-console">
        <div
          v-for="(line, i) in filteredLines"
          :key="i"
          class="log-line"
          :class="lineClass(line)"
        ><span class="ln mono">{{ String(i + 1).padStart(3, '0') }}</span><span class="lt">{{ line }}</span></div>
        <span v-if="!filteredLines.length" class="log-empty mono">
          {{ logQuery ? '没有匹配的日志行' : '等待日志输出…' }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import {
  Back,
  Bottom,
  Search,
  Monitor,
  CopyDocument,
  Download,
  RefreshRight,
} from '@element-plus/icons-vue'
import api, { getToken } from '../api/client'

const route = useRoute()
const router = useRouter()
const runId = route.params.runId

// 工作区内（/projects/:id/runs/:runId）为项目作用域
const scopedProjectId = route.params.id || null
const scoped = !!scopedProjectId

function detailRoute(id) {
  return scoped
    ? { name: 'project-run-detail', params: { id: scopedProjectId, runId: id } }
    : { name: 'run-detail', params: { runId: id } }
}
function goBack() {
  if (scoped) router.push({ name: 'project-runs', params: { id: scopedProjectId } })
  else router.push({ name: 'runs' })
}

const loading = ref(false)
const run = ref({})
const lines = ref([])
const connected = ref(false)
const consoleRef = ref()
const logQuery = ref('')
const autoScroll = ref(true)
let ws = null

const filteredLines = computed(() => {
  if (!logQuery.value) return lines.value
  const q = logQuery.value.toLowerCase()
  return lines.value.filter((l) => l.toLowerCase().includes(q))
})

const exitTone = computed(() => {
  if (run.value.exit_code == null) return ''
  return run.value.exit_code === 0 ? 'ok' : 'danger'
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
function lineClass(line) {
  if (line.startsWith('[平台]')) return 'log-platform'
  const l = line.toLowerCase()
  if (/passed|✓|成功|ok\b/.test(l)) return 'log-pass'
  if (/failed|error|✗|失败|traceback/.test(l)) return 'log-fail'
  return ''
}

function scrollBottom() {
  if (!autoScroll.value) return
  nextTick(() => {
    if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
  })
}
// 去除 pytest 等工具输出的 ANSI 颜色转义序列，避免日志出现乱码方块
// eslint-disable-next-line no-control-regex
const ANSI_RE = /[\u001b\u009b][[()#;?]*(?:[0-9]{1,4}(?:;[0-9]{0,4})*)?[0-9A-ORZcf-nqry=><]/g
function stripAnsi(text) {
  return text.replace(ANSI_RE, '')
}
function appendLine(line) {
  lines.value.push(stripAnsi(line))
  scrollBottom()
}

function copyLog() {
  navigator.clipboard.writeText(lines.value.join('\n')).then(() => ElMessage.success('已复制日志'))
}
function downloadLog() {
  const blob = new Blob([lines.value.join('\n')], { type: 'text/plain' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `run-${runId}.log`
  a.click()
  URL.revokeObjectURL(url)
}

async function doRerun() {
  try {
    const { data } = await api.post(`/runs/${runId}/rerun`)
    ElMessage.success(`已发起重跑 #${data.id}`)
    router.push(detailRoute(data.id))
    setTimeout(() => router.go(0), 50)
  } catch {
    /* handled globally */
  }
}

async function loadRun() {
  loading.value = true
  try {
    const { data } = await api.get(`/runs/${runId}`)
    run.value = data
  } finally {
    loading.value = false
  }
}

function connect() {
  const proto = location.protocol === 'https:' ? 'wss' : 'ws'
  const token = encodeURIComponent(getToken())
  const url = `${proto}://${location.host}/api/runs/${runId}/stream?token=${token}`
  ws = new WebSocket(url)

  ws.onopen = () => {
    connected.value = true
  }
  ws.onmessage = (event) => {
    let payload = null
    try {
      payload = JSON.parse(event.data)
    } catch {
      payload = null
    }
    if (payload && payload.event === 'end') {
      run.value.status = payload.status
      run.value.exit_code = payload.exit_code
      connected.value = false
      ws && ws.close()
      loadRun()
      return
    }
    appendLine(event.data)
  }
  ws.onclose = () => {
    connected.value = false
  }
  ws.onerror = () => {
    connected.value = false
  }
}

onMounted(async () => {
  await loadRun()
  connect()
})

onBeforeUnmount(() => {
  if (ws) ws.close()
})
</script>

<style scoped>
.cmd {
  color: var(--ink-soft);
  font-size: 12px;
  margin-top: 8px;
  background: var(--panel-tint);
  border: 1px solid var(--line);
  border-radius: 5px;
  padding: 6px 10px;
  display: inline-block;
  max-width: 100%;
  overflow-x: auto;
  white-space: nowrap;
}

.meta-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 1px;
  background: var(--border);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  margin-bottom: 16px;
}
@media (max-width: 760px) {
  .meta-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
.meta-item {
  background: var(--panel);
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.meta-label {
  font-size: 9.5px;
}
.meta-val {
  font-size: 14px;
  font-weight: 550;
}
.meta-val.key {
  color: var(--brand-strong);
  font-weight: 600;
}
.meta-val.ok {
  color: var(--ok);
}
.meta-val.danger {
  color: var(--danger);
}

.log-head {
  padding: 11px 14px;
}
.log-title {
  display: flex;
  align-items: center;
  gap: 9px;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 600;
  font-size: 14px;
}
.log-title .el-icon {
  color: var(--ink-soft);
}
.live-tag {
  color: var(--ok);
  font-size: 11px;
  animation: pulse 1.4s infinite;
}
.line-count {
  font-size: 11px;
  color: var(--ink-faint);
  font-weight: 400;
}
@keyframes pulse {
  50% {
    opacity: 0.4;
  }
}

.log-tools {
  display: flex;
  align-items: center;
  gap: 6px;
}
.log-search {
  display: flex;
  align-items: center;
  gap: 6px;
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 0 8px;
  height: 30px;
  width: 180px;
  color: var(--ink-faint);
  font-size: 12px;
}
.log-search:focus-within {
  border-color: var(--brand-border);
}
.log-search input {
  border: none;
  outline: none;
  background: none;
  flex: 1;
  font-size: 12.5px;
  color: var(--ink);
  font-family: inherit;
  min-width: 0;
}
.tool-btn {
  width: 30px;
  height: 30px;
  border: 1px solid var(--border);
  background: var(--panel);
  border-radius: 6px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--ink-soft);
  transition: all 0.14s;
}
.tool-btn:hover {
  border-color: var(--border-strong);
  color: var(--ink);
}
.tool-btn.on {
  background: var(--brand-soft);
  border-color: var(--brand-border);
  color: var(--brand-strong);
}

.log-console {
  height: 520px;
  border-radius: 0;
  border: none;
}
.log-line {
  display: flex;
  gap: 14px;
}
.ln {
  color: #5a534a;
  user-select: none;
  flex-shrink: 0;
  font-size: 11px;
  padding-top: 1px;
}
.lt {
  flex: 1;
  white-space: pre-wrap;
  word-break: break-word;
}
.log-empty {
  color: #6d645a;
}
</style>
