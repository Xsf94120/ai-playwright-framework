<template>
  <div>
    <div class="page-header">
      <div>
        <h2 class="page-title">执行记录</h2>
        <p class="page-subtitle">触发测试运行、AI 用例生成，并查看实时日志与历史结果</p>
      </div>
      <el-button type="primary" :icon="VideoPlay" @click="openRun">运行测试</el-button>
    </div>

    <div class="panel" v-loading="loading">
      <el-table :data="runs" stripe @row-click="goDetail" class="clickable">
        <el-table-column label="#" width="70">
          <template #default="{ row }"><span class="mono">{{ row.id }}</span></template>
        </el-table-column>
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag size="small" :type="row.kind === 'generate' ? 'warning' : ''">
              {{ row.kind === 'generate' ? '生成' : '运行' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="项目" width="140">
          <template #default="{ row }"><span class="mono">{{ row.project_key }}</span></template>
        </el-table-column>
        <el-table-column label="用例集" min-width="140">
          <template #default="{ row }">
            <span class="mono">{{ row.suite_name || '全部' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="环境/浏览器" width="160">
          <template #default="{ row }">
            <span class="muted">{{ row.env }} · {{ row.browser }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag size="small" :type="statusType(row.status)">{{ statusText(row.status) }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="时间" width="170">
          <template #default="{ row }">
            <span class="muted">{{ fmt(row.created_at) }}</span>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" title="运行测试" width="520">
      <el-form :model="runForm" label-width="92px">
        <el-form-item label="项目">
          <el-select v-model="runForm.project_id" style="width: 100%" @change="onProjectChange">
            <el-option
              v-for="p in projects"
              :key="p.id"
              :label="`${p.name} (${p.key})`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="用例集">
          <el-select v-model="runForm.suite_name" clearable placeholder="留空运行全部" style="width: 100%">
            <el-option v-for="s in suites" :key="s.id" :label="s.name" :value="s.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="runForm.env" style="width: 100%">
            <el-option v-for="e in envOptions" :key="e" :label="e" :value="e" />
          </el-select>
        </el-form-item>
        <el-form-item label="AI 模式">
          <el-radio-group v-model="runForm.ai_mode">
            <el-radio-button value="strict">strict 严格</el-radio-button>
            <el-radio-button value="assist">assist 辅助</el-radio-button>
            <el-radio-button value="off">off 关闭</el-radio-button>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="浏览器">
          <el-select v-model="runForm.browser" style="width: 100%">
            <el-option label="chromium" value="chromium" />
            <el-option label="firefox" value="firefox" />
            <el-option label="webkit" value="webkit" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="submitting" @click="submitRun">开始运行</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import api from '../api/client'

const route = useRoute()
const router = useRouter()

const runs = ref([])
const projects = ref([])
const suites = ref([])
const loading = ref(false)
const submitting = ref(false)
const dialogVisible = ref(false)

const runForm = reactive({
  project_id: null,
  suite_name: '',
  env: 'prod',
  ai_mode: 'strict',
  browser: 'chromium',
})

const envOptions = computed(() => {
  const p = projects.value.find((x) => x.id === runForm.project_id)
  return p && p.environments.length ? p.environments.map((e) => e.name) : ['prod']
})

function statusType(s) {
  return { passed: 'success', failed: 'danger', running: 'warning', pending: 'info' }[s] || 'info'
}
function statusText(s) {
  return { passed: '通过', failed: '失败', running: '运行中', pending: '排队中' }[s] || s
}
function fmt(t) {
  return t ? new Date(t).toLocaleString('zh-CN') : '—'
}

async function loadRuns() {
  loading.value = true
  try {
    const params = route.query.project ? { project_id: route.query.project } : {}
    const { data } = await api.get('/runs', { params })
    runs.value = data
  } finally {
    loading.value = false
  }
}

async function loadProjects() {
  const { data } = await api.get('/projects')
  projects.value = data
}

async function loadSuites(projectId) {
  if (!projectId) {
    suites.value = []
    return
  }
  const { data } = await api.get(`/projects/${projectId}/suites`)
  suites.value = data
}

function onProjectChange(id) {
  runForm.suite_name = ''
  runForm.env = 'prod'
  loadSuites(id)
}

async function openRun() {
  await loadProjects()
  const preset = route.query.project ? Number(route.query.project) : projects.value[0]?.id
  runForm.project_id = preset || null
  runForm.suite_name = route.query.suite || ''
  if (preset) await loadSuites(preset)
  dialogVisible.value = true
}

async function submitRun() {
  if (!runForm.project_id) {
    ElMessage.warning('请选择项目')
    return
  }
  submitting.value = true
  try {
    const { data } = await api.post('/runs', { ...runForm })
    dialogVisible.value = false
    router.push({ name: 'run-detail', params: { runId: data.id } })
  } finally {
    submitting.value = false
  }
}

function goDetail(row) {
  router.push({ name: 'run-detail', params: { runId: row.id } })
}

onMounted(async () => {
  await Promise.all([loadRuns(), loadProjects()])
})
</script>

<style scoped>
.clickable :deep(.el-table__row) {
  cursor: pointer;
}
</style>
