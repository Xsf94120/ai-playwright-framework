<template>
  <div v-loading="loading">
    <div class="page-header">
      <div>
        <h2 class="page-title">{{ isNew ? '新建用例集' : '编辑用例集' }}</h2>
        <p class="page-subtitle">分层配置：自然语言步骤、元素定位、测试数据、模块与变量</p>
      </div>
      <div class="flex gap-8">
        <el-button :icon="Back" @click="goBack">返回</el-button>
        <el-button v-if="!isNew" type="success" :icon="MagicStick" :loading="generating" @click="generate">
          AI 生成用例
        </el-button>
        <el-button type="primary" :icon="Check" :loading="saving" @click="save">保存</el-button>
      </div>
    </div>

    <div class="panel mb">
      <el-form :model="meta" label-width="90px" style="max-width: 720px">
        <el-form-item label="名称">
          <el-input
            v-model="meta.name"
            :disabled="!isNew"
            placeholder="字母/数字/下划线，如：login_flow"
            class="mono"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="meta.description" placeholder="用例集说明（可选）" />
        </el-form-item>
      </el-form>
    </div>

    <el-tabs v-model="activeLayer" type="border-card">
      <!-- generation -->
      <el-tab-pane name="generation">
        <template #label>
          <span>步骤描述<el-tag v-if="hasContent('generation')" size="small" type="success" class="dot">●</el-tag></span>
        </template>
        <div class="mode-bar">
          <el-radio-group v-model="genMode" size="small" @change="onGenModeChange">
            <el-radio-button value="form">结构化表单</el-radio-button>
            <el-radio-button value="yaml">YAML 源码</el-radio-button>
          </el-radio-group>
        </div>
        <GenerationEditor v-if="genMode === 'form'" v-model="genCases" />
        <YamlBox v-else v-model="layers.generation" placeholder="cases: [...]" />
      </el-tab-pane>

      <!-- elements -->
      <el-tab-pane name="elements">
        <template #label>
          <span>元素定位<el-tag v-if="hasContent('elements')" size="small" type="success" class="dot">●</el-tag></span>
        </template>
        <div class="mode-bar">
          <el-radio-group v-model="elMode" size="small" @change="onElModeChange">
            <el-radio-button value="form">结构化表单</el-radio-button>
            <el-radio-button value="yaml">YAML 源码</el-radio-button>
          </el-radio-group>
        </div>
        <ElementsEditor v-if="elMode === 'form'" v-model="elRows" />
        <YamlBox v-else v-model="layers.elements" placeholder="username_input: '#user-name'" />
      </el-tab-pane>

      <!-- cases -->
      <el-tab-pane name="cases">
        <template #label>
          <span>用例 cases<el-tag v-if="hasContent('cases')" size="small" type="success" class="dot">●</el-tag></span>
        </template>
        <el-alert type="info" :closable="false" class="mb"
          title="已落地的可执行用例（cases 层）。AI 生成成功后会自动写入此处。" />
        <YamlBox v-model="layers.cases" />
      </el-tab-pane>

      <!-- data -->
      <el-tab-pane name="data">
        <template #label>
          <span>测试数据<el-tag v-if="hasContent('data')" size="small" type="success" class="dot">●</el-tag></span>
        </template>
        <el-alert type="info" :closable="false" class="mb" title="参数化测试数据（data 层）。" />
        <YamlBox v-model="layers.data" />
      </el-tab-pane>

      <!-- modules -->
      <el-tab-pane name="modules">
        <template #label>
          <span>模块 modules<el-tag v-if="hasContent('modules')" size="small" type="success" class="dot">●</el-tag></span>
        </template>
        <el-alert type="info" :closable="false" class="mb" title="可复用步骤模块（modules 层）。" />
        <YamlBox v-model="layers.modules" />
      </el-tab-pane>

      <!-- vars -->
      <el-tab-pane name="vars">
        <template #label>
          <span>变量 vars<el-tag v-if="hasContent('vars')" size="small" type="success" class="dot">●</el-tag></span>
        </template>
        <el-alert type="info" :closable="false" class="mb" title="全局/共享变量（vars 层）。" />
        <YamlBox v-model="layers.vars" />
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, Check, MagicStick } from '@element-plus/icons-vue'
import api from '../api/client'
import { dumpYaml, safeParse } from '../utils/yaml'
import GenerationEditor from '../components/GenerationEditor.vue'
import ElementsEditor from '../components/ElementsEditor.vue'
import YamlBox from '../components/YamlBox.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id
const suiteId = route.params.suiteId
const isNew = computed(() => !suiteId)

const loading = ref(false)
const saving = ref(false)
const generating = ref(false)
const activeLayer = ref('generation')

const meta = reactive({ name: '', description: '' })
const layers = reactive({
  generation: '',
  elements: '',
  cases: '',
  data: '',
  modules: '',
  vars: '',
})

const genMode = ref('form')
const elMode = ref('form')
const genCases = ref([])
const elRows = ref([])

function hasContent(layer) {
  if (layer === 'generation' && genMode.value === 'form') return genCases.value.length > 0
  if (layer === 'elements' && elMode.value === 'form') return elRows.value.length > 0
  return !!(layers[layer] && layers[layer].trim())
}

// ---- structured <-> yaml conversions ----
function genToStructured(text) {
  const { value, error } = safeParse(text)
  if (error) return []
  const list = value?.cases || []
  return list.map((c) => ({
    name: c.name || '',
    description: c.description || '',
    steps: Array.isArray(c.steps) ? [...c.steps] : [],
    checkpoints: Array.isArray(c.checkpoints) ? [...c.checkpoints] : [],
    final: c.final || '',
  }))
}

function genToYaml(cases) {
  if (!cases.length) return ''
  const obj = {
    cases: cases.map((c) => {
      const o = { name: c.name }
      if (c.description) o.description = c.description
      o.steps = (c.steps || []).filter((s) => s && s.trim())
      const cps = (c.checkpoints || []).filter((s) => s && s.trim())
      if (cps.length) o.checkpoints = cps
      if (c.final && c.final.trim()) o.final = c.final
      return o
    }),
  }
  return dumpYaml(obj)
}

function elToStructured(text) {
  const { value, error } = safeParse(text)
  if (error || !value || typeof value !== 'object') return []
  return Object.entries(value).map(([name, selector]) => ({
    name,
    selector: typeof selector === 'string' ? selector : JSON.stringify(selector),
  }))
}

function elToYaml(rows) {
  const valid = rows.filter((r) => r.name && r.name.trim())
  if (!valid.length) return ''
  const obj = {}
  for (const r of valid) obj[r.name] = r.selector
  return dumpYaml(obj)
}

function onGenModeChange(mode) {
  if (mode === 'yaml') {
    layers.generation = genToYaml(genCases.value)
  } else {
    genCases.value = genToStructured(layers.generation)
  }
}
function onElModeChange(mode) {
  if (mode === 'yaml') {
    layers.elements = elToYaml(elRows.value)
  } else {
    elRows.value = elToStructured(layers.elements)
  }
}

function syncStructuredToLayers() {
  if (genMode.value === 'form') layers.generation = genToYaml(genCases.value)
  if (elMode.value === 'form') layers.elements = elToYaml(elRows.value)
}

async function load() {
  if (isNew.value) {
    genCases.value = []
    elRows.value = []
    return
  }
  loading.value = true
  try {
    const { data } = await api.get(`/projects/${projectId}/suites/${suiteId}`)
    meta.name = data.name
    meta.description = data.description
    layers.generation = data.generation_yaml || ''
    layers.elements = data.elements_yaml || ''
    layers.cases = data.cases_yaml || ''
    layers.data = data.data_yaml || ''
    layers.modules = data.modules_yaml || ''
    layers.vars = data.vars_yaml || ''
    genCases.value = genToStructured(layers.generation)
    elRows.value = elToStructured(layers.elements)
  } finally {
    loading.value = false
  }
}

function buildPayload() {
  syncStructuredToLayers()
  return {
    cases_yaml: layers.cases,
    data_yaml: layers.data,
    elements_yaml: layers.elements,
    modules_yaml: layers.modules,
    vars_yaml: layers.vars,
    generation_yaml: layers.generation,
    description: meta.description,
  }
}

async function save() {
  if (isNew.value && !/^[A-Za-z][A-Za-z0-9_]*$/.test(meta.name)) {
    ElMessage.warning('请填写合法的用例集名称（字母开头，仅含字母/数字/下划线）')
    return
  }
  saving.value = true
  try {
    const payload = buildPayload()
    if (isNew.value) {
      const { data } = await api.post(`/projects/${projectId}/suites`, {
        name: meta.name,
        ...payload,
      })
      ElMessage.success('用例集已创建')
      router.replace({ name: 'suite-edit', params: { id: projectId, suiteId: data.id } })
    } else {
      await api.put(`/projects/${projectId}/suites/${suiteId}`, payload)
      ElMessage.success('已保存')
    }
  } finally {
    saving.value = false
  }
}

async function generate() {
  generating.value = true
  try {
    await api.put(`/projects/${projectId}/suites/${suiteId}`, buildPayload())
    const { data } = await api.post('/generate', {
      project_id: Number(projectId),
      suite_name: meta.name,
    })
    ElMessage.success('已提交 AI 生成任务')
    router.push({ name: 'run-detail', params: { runId: data.id } })
  } finally {
    generating.value = false
  }
}

function goBack() {
  router.push({ name: 'project-detail', params: { id: projectId } })
}

onMounted(load)
</script>

<style scoped>
.mb {
  margin-bottom: 16px;
}
.mode-bar {
  margin-bottom: 16px;
}
.dot {
  margin-left: 6px;
  border: none;
  background: transparent;
  color: var(--brand);
  padding: 0;
}
</style>
