<template>
  <div v-loading="loading">
    <div class="page-header">
      <div>
        <h2 class="page-title">
          {{ project.name }}
          <el-tag size="small" type="info" class="mono">{{ project.key }}</el-tag>
        </h2>
        <p class="page-subtitle">{{ project.description || '配置项目环境、模型与用例集' }}</p>
      </div>
      <div class="flex gap-8">
        <el-button :icon="VideoPlay" @click="goRuns">前往执行</el-button>
        <el-button :icon="Back" @click="$router.push({ name: 'projects' })">返回</el-button>
      </div>
    </div>

    <el-tabs v-model="activeTab" class="detail-tabs">
      <!-- 基本信息与环境 -->
      <el-tab-pane label="基本信息 / 环境" name="basic">
        <div class="panel">
          <el-form :model="form" label-width="110px" style="max-width: 720px">
            <el-form-item label="项目名称">
              <el-input v-model="form.name" />
            </el-form-item>
            <el-form-item label="描述">
              <el-input v-model="form.description" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="视口尺寸">
              <div class="flex gap-8">
                <el-input-number v-model="form.viewport_width" :min="320" :max="3840" />
                <span class="muted">×</span>
                <el-input-number v-model="form.viewport_height" :min="320" :max="2160" />
              </div>
            </el-form-item>
            <el-form-item label="Tracing">
              <el-select v-model="form.tracing" style="width: 240px">
                <el-option label="off 关闭" value="off" />
                <el-option label="on 始终录制" value="on" />
                <el-option label="retain-on-failure 失败保留" value="retain-on-failure" />
              </el-select>
            </el-form-item>
            <el-form-item label="环境地址">
              <div style="width: 100%">
                <div v-for="(env, i) in form.environments" :key="i" class="env-row">
                  <el-input v-model="env.name" placeholder="环境名" style="width: 120px" />
                  <el-input v-model="env.base_url" placeholder="https://..." />
                  <el-button :icon="Delete" text @click="form.environments.splice(i, 1)" />
                </div>
                <el-button size="small" :icon="Plus" @click="form.environments.push({ name: '', base_url: '' })">
                  添加环境
                </el-button>
              </div>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingBasic" @click="saveBasic">
                保存基本信息
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- LLM 配置 -->
      <el-tab-pane label="模型 (LLM) 配置" name="llm">
        <div class="panel">
          <el-alert
            type="info"
            :closable="false"
            title="此处配置驱动 AI 用例生成与智能执行的大模型接口，物化为引擎运行时的 .env 变量。"
            class="mb"
          />
          <el-form :model="llm" label-width="140px" style="max-width: 720px">
            <el-form-item label="Base URL">
              <el-input v-model="llm.base_url" placeholder="https://api.openai.com/v1" />
            </el-form-item>
            <el-form-item label="API Key">
              <el-input
                v-model="llm.api_key"
                type="password"
                show-password
                :placeholder="llm.api_key_set ? '已配置（留空则保持不变）' : '请输入 API Key'"
              />
            </el-form-item>
            <el-form-item label="模型名称">
              <el-input v-model="llm.model" placeholder="如：gpt-4o-mini" />
            </el-form-item>
            <el-form-item label="推理强度">
              <el-select v-model="llm.reasoning_effort" style="width: 200px">
                <el-option label="low" value="low" />
                <el-option label="medium" value="medium" />
                <el-option label="high" value="high" />
              </el-select>
            </el-form-item>
            <el-form-item label="响应格式">
              <el-select v-model="llm.response_format" style="width: 200px">
                <el-option label="auto" value="auto" />
                <el-option label="json_object" value="json_object" />
                <el-option label="text" value="text" />
              </el-select>
            </el-form-item>
            <el-form-item label="超时(秒)">
              <el-input-number v-model="llm.timeout_seconds" :min="5" :max="600" />
            </el-form-item>
            <el-form-item label="数据策略">
              <el-select v-model="llm.data_policy" style="width: 200px">
                <el-option label="external 外部模型" value="external" />
                <el-option label="internal 内部/私有" value="internal" />
              </el-select>
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingLlm" @click="saveLlm">
                保存模型配置
              </el-button>
            </el-form-item>
          </el-form>
        </div>
      </el-tab-pane>

      <!-- AI 运行时配置 YAML -->
      <el-tab-pane label="AI 运行时配置" name="ai">
        <div class="panel">
          <el-alert
            type="info"
            :closable="false"
            title="对应引擎的 config/ai_config.yaml，控制 AI 执行模式、重试、断言策略等。"
            class="mb"
          />
          <el-input
            v-model="aiConfig"
            type="textarea"
            :rows="20"
            class="mono yaml-area"
            spellcheck="false"
          />
          <div class="flex gap-8" style="margin-top: 14px">
            <el-button type="primary" :loading="savingAi" @click="saveAi">
              保存运行时配置
            </el-button>
            <el-button @click="loadAi">重置</el-button>
          </div>
        </div>
      </el-tab-pane>

      <!-- 用例集 -->
      <el-tab-pane label="用例集" name="suites">
        <div class="panel">
          <div class="flex-between mb">
            <span class="muted">
              用例集对应引擎的分层 YAML（cases / data / elements / modules / vars / generation）
            </span>
            <el-button type="primary" :icon="Plus" @click="newSuite">新建用例集</el-button>
          </div>
          <el-table :data="suites" stripe v-loading="loadingSuites">
            <el-table-column prop="name" label="名称" min-width="180">
              <template #default="{ row }">
                <span class="mono">{{ row.name }}</span>
              </template>
            </el-table-column>
            <el-table-column prop="description" label="描述" min-width="240">
              <template #default="{ row }">
                {{ row.description || '—' }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" align="right">
              <template #default="{ row }">
                <el-button text type="primary" @click="editSuite(row)">编辑</el-button>
                <el-button text type="primary" @click="runSuite(row)">运行</el-button>
                <el-button text type="danger" @click="removeSuite(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete, Back, VideoPlay } from '@element-plus/icons-vue'
import api from '../api/client'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id

const loading = ref(false)
const loadingSuites = ref(false)
const savingBasic = ref(false)
const savingLlm = ref(false)
const savingAi = ref(false)
const activeTab = ref('basic')

const project = ref({})
const form = reactive({
  name: '',
  description: '',
  viewport_width: 1280,
  viewport_height: 720,
  tracing: 'off',
  environments: [],
})
const llm = reactive({
  base_url: '',
  api_key: '',
  model: '',
  reasoning_effort: 'medium',
  response_format: 'auto',
  timeout_seconds: 60,
  data_policy: 'external',
  api_key_set: false,
})
const aiConfig = ref('')
const suites = ref([])

async function loadProject() {
  loading.value = true
  try {
    const { data } = await api.get(`/projects/${projectId}`)
    project.value = data
    Object.assign(form, {
      name: data.name,
      description: data.description,
      viewport_width: data.viewport_width,
      viewport_height: data.viewport_height,
      tracing: data.tracing,
      environments: data.environments.map((e) => ({ name: e.name, base_url: e.base_url })),
    })
  } finally {
    loading.value = false
  }
}

async function loadLlm() {
  const { data } = await api.get(`/projects/${projectId}/llm`)
  Object.assign(llm, data, { api_key: '' })
}

async function loadAi() {
  const { data } = await api.get(`/projects/${projectId}/ai-config`)
  aiConfig.value = data.content_yaml
}

async function loadSuites() {
  loadingSuites.value = true
  try {
    const { data } = await api.get(`/projects/${projectId}/suites`)
    suites.value = data
  } finally {
    loadingSuites.value = false
  }
}

async function saveBasic() {
  savingBasic.value = true
  try {
    await api.put(`/projects/${projectId}`, {
      ...form,
      environments: form.environments.filter((e) => e.name.trim()),
    })
    ElMessage.success('已保存')
    await loadProject()
  } finally {
    savingBasic.value = false
  }
}

async function saveLlm() {
  savingLlm.value = true
  try {
    await api.put(`/projects/${projectId}/llm`, { ...llm })
    ElMessage.success('模型配置已保存')
    await loadLlm()
  } finally {
    savingLlm.value = false
  }
}

async function saveAi() {
  savingAi.value = true
  try {
    await api.put(`/projects/${projectId}/ai-config`, { content_yaml: aiConfig.value })
    ElMessage.success('运行时配置已保存')
  } finally {
    savingAi.value = false
  }
}

function newSuite() {
  router.push({ name: 'suite-new', params: { id: projectId } })
}
function editSuite(row) {
  router.push({ name: 'suite-edit', params: { id: projectId, suiteId: row.id } })
}
function runSuite(row) {
  router.push({ name: 'runs', query: { project: projectId, suite: row.name } })
}
async function removeSuite(row) {
  await ElMessageBox.confirm(`确定删除用例集「${row.name}」吗？`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await api.delete(`/projects/${projectId}/suites/${row.id}`)
  ElMessage.success('已删除')
  await loadSuites()
}

function goRuns() {
  router.push({ name: 'runs', query: { project: projectId } })
}

onMounted(async () => {
  await Promise.all([loadProject(), loadLlm(), loadAi(), loadSuites()])
})
</script>

<style scoped>
.detail-tabs :deep(.el-tabs__header) {
  margin-bottom: 16px;
}
.env-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.mb {
  margin-bottom: 16px;
}
.yaml-area :deep(textarea) {
  font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
  font-size: 12.5px;
  line-height: 1.6;
}
</style>
