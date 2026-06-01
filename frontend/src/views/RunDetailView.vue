<template>
  <div v-loading="loading">
    <div class="page-header">
      <div>
        <h2 class="page-title">
          运行 #{{ run.id }}
          <span class="badge" :class="[statusTone(run.status), run.status === 'running' ? 'live' : '']">
            <span class="dot" />{{ statusText(run.status) }}
          </span>
          <span class="badge" :class="run.kind === 'generate' ? 'warn' : 'info'">
            {{ run.kind === 'generate' ? 'AI 生成' : '测试运行' }}
          </span>
        </h2>
        <p class="page-subtitle mono">{{ run.command || '准备中...' }}</p>
      </div>
      <el-button :icon="Back" @click="$router.push({ name: 'runs' })">返回列表</el-button>
    </div>

    <div class="meta-grid">
      <div class="meta-item">
        <span class="meta-label">项目</span>
        <span class="mono">{{ run.project_key }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">用例集</span>
        <span class="mono">{{ run.suite_name || '全部' }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">环境</span>
        <span>{{ run.env }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">浏览器</span>
        <span>{{ run.browser }}</span>
      </div>
      <div class="meta-item">
        <span class="meta-label">退出码</span>
        <span class="mono">{{ run.exit_code ?? '—' }}</span>
      </div>
    </div>

    <div class="panel">
      <div class="flex-between mb">
        <span class="log-title">
          实时日志
          <span v-if="connected" class="live">● LIVE</span>
        </span>
        <el-button size="small" text :icon="Bottom" @click="scrollBottom">滚到底部</el-button>
      </div>
      <div ref="consoleRef" class="log-console">
        <span
          v-for="(line, i) in lines"
          :key="i"
          class="log-line"
          :class="{ 'log-platform': line.startsWith('[平台]') }"
        >{{ line }}</span>
        <span v-if="!lines.length" class="muted">等待日志输出...</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { Back, Bottom } from '@element-plus/icons-vue'
import api, { getToken } from '../api/client'

const route = useRoute()
const runId = route.params.runId

const loading = ref(false)
const run = ref({})
const lines = ref([])
const connected = ref(false)
const consoleRef = ref()
let ws = null

function statusTone(s) {
  return { passed: 'ok', failed: 'danger', running: 'warn', pending: 'neutral' }[s] || 'neutral'
}
function statusText(s) {
  return { passed: '通过', failed: '失败', running: '运行中', pending: '排队中' }[s] || s
}

function scrollBottom() {
  nextTick(() => {
    if (consoleRef.value) consoleRef.value.scrollTop = consoleRef.value.scrollHeight
  })
}

function appendLine(line) {
  lines.value.push(line)
  scrollBottom()
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
.meta-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 12px;
  margin-bottom: 20px;
}
.meta-item {
  background: #fff;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 12px 14px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.meta-label {
  font-size: 12px;
  color: var(--ink-soft);
}
.log-title {
  font-weight: 600;
}
.live {
  color: #57c08d;
  font-size: 12px;
  margin-left: 8px;
  animation: pulse 1.4s infinite;
}
@keyframes pulse {
  50% {
    opacity: 0.4;
  }
}
.mb {
  margin-bottom: 12px;
}
</style>
