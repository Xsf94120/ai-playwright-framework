<template>
  <div v-loading="loading" class="editor">
    <!-- 操作头 -->
    <header class="edit-head">
      <div class="head-left">
        <button class="back-btn" @click="goBack"><el-icon><Back /></el-icon></button>
        <div>
          <h2 class="edit-title">{{ isNew ? '新建用例集' : meta.name || '编辑用例集' }}</h2>
          <p class="edit-sub">用自然语言描述步骤，AI 生成可执行用例</p>
        </div>
      </div>
      <div class="head-actions">
        <el-button :icon="Check" :loading="saving" @click="save">保存</el-button>
        <el-button
          v-if="!isNew"
          type="primary"
          :icon="MagicStick"
          :loading="generating"
          @click="generate"
        >
          AI 生成用例
        </el-button>
      </div>
    </header>

    <!-- 用例集信息 -->
    <section class="panel step">
      <div class="step-head">
        <span class="step-no">1</span>
        <div>
          <h3 class="step-title">用例集信息</h3>
          <p class="step-hint">名称用于在运行时引用，创建后不可修改</p>
        </div>
      </div>
      <el-form :model="meta" label-width="72px" style="max-width: 600px">
        <el-form-item label="名称">
          <el-input
            v-model="meta.name"
            :disabled="!isNew"
            placeholder="字母开头，仅含字母/数字/下划线，如 login_flow"
            class="mono"
          />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="meta.description" placeholder="用例集说明（可选）" />
        </el-form-item>
      </el-form>
    </section>

    <!-- 步骤描述 -->
    <section class="panel step">
      <div class="step-head">
        <span class="step-no">2</span>
        <div class="step-head-main">
          <div>
            <h3 class="step-title">描述测试步骤</h3>
            <p class="step-hint">每条用例用自然语言写明步骤与校验点（generation 层）</p>
          </div>
          <el-radio-group v-model="genMode" size="small" @change="onGenModeChange">
            <el-radio-button value="form">表单</el-radio-button>
            <el-radio-button value="yaml">YAML</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      <GenerationEditor v-if="genMode === 'form'" v-model="genCases" />
      <YamlBox v-else v-model="layers.generation" placeholder="cases: [...]" />

      <div v-if="isNew" class="gen-tip">
        <el-icon><InfoFilled /></el-icon>
        <span>保存用例集后即可使用「AI 生成用例」，将上述描述转换为可执行用例。</span>
      </div>
      <div v-else class="gen-action">
        <el-button type="primary" :icon="MagicStick" :loading="generating" @click="generate">
          AI 生成可执行用例
        </el-button>
        <span class="gen-action-hint">会先保存当前描述，再提交生成任务</span>
      </div>
    </section>

    <!-- 可执行用例 -->
    <section class="panel step">
      <div class="step-head">
        <span class="step-no">3</span>
        <div>
          <h3 class="step-title">
            可执行用例
            <el-tag v-if="hasContent('cases')" size="small" type="success" effect="light">已生成</el-tag>
            <el-tag v-else size="small" type="info" effect="light">待生成</el-tag>
          </h3>
          <p class="step-hint">最终运行的用例（cases 层）。AI 生成成功后会自动写入，也可手动编辑</p>
        </div>
      </div>
      <YamlBox v-model="layers.cases" placeholder="AI 生成后将填充此处，或手动编写 cases YAML" />
    </section>

    <!-- 高级配置 -->
    <section class="panel step">
      <div class="step-head">
        <span class="step-no muted-no">+</span>
        <div>
          <h3 class="step-title">高级配置</h3>
          <p class="step-hint">元素定位、测试数据、可复用模块与变量（按需填写）</p>
        </div>
      </div>
      <el-collapse v-model="openAdvanced">
        <el-collapse-item name="elements">
          <template #title>
            <span class="adv-title">元素定位<span v-if="hasContent('elements')" class="adv-dot" /></span>
          </template>
          <div class="mode-bar">
            <el-radio-group v-model="elMode" size="small" @change="onElModeChange">
              <el-radio-button value="form">表单</el-radio-button>
              <el-radio-button value="yaml">YAML</el-radio-button>
            </el-radio-group>
          </div>
          <ElementsEditor v-if="elMode === 'form'" v-model="elRows" />
          <YamlBox v-else v-model="layers.elements" placeholder="username_input: '#user-name'" />
        </el-collapse-item>

        <el-collapse-item name="data">
          <template #title>
            <span class="adv-title">测试数据<span v-if="hasContent('data')" class="adv-dot" /></span>
          </template>
          <YamlBox v-model="layers.data" placeholder="参数化测试数据（data 层）" />
        </el-collapse-item>

        <el-collapse-item name="modules">
          <template #title>
            <span class="adv-title">模块<span v-if="hasContent('modules')" class="adv-dot" /></span>
          </template>
          <YamlBox v-model="layers.modules" placeholder="可复用步骤模块（modules 层）" />
        </el-collapse-item>

        <el-collapse-item name="vars">
          <template #title>
            <span class="adv-title">变量<span v-if="hasContent('vars')" class="adv-dot" /></span>
          </template>
          <YamlBox v-model="layers.vars" placeholder="全局/共享变量（vars 层）" />
        </el-collapse-item>
      </el-collapse>
    </section>
  </div>
</template>

<script setup>
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Back, Check, MagicStick, InfoFilled } from '@element-plus/icons-vue'
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
const openAdvanced = ref([])

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
  if (mode === 'yaml') layers.generation = genToYaml(genCases.value)
  else genCases.value = genToStructured(layers.generation)
}
function onElModeChange(mode) {
  if (mode === 'yaml') layers.elements = elToYaml(elRows.value)
  else elRows.value = elToStructured(layers.elements)
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
    // 自动展开有内容的高级层
    openAdvanced.value = ['elements', 'data', 'modules', 'vars'].filter((l) =>
      (layers[l] || '').trim()
    )
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
    router.push({
      name: 'project-run-detail',
      params: { id: projectId, runId: data.id },
    })
  } finally {
    generating.value = false
  }
}

function goBack() {
  router.push({ name: 'project-suites', params: { id: projectId } })
}

onMounted(load)
</script>

<style scoped>
.editor {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.edit-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}
.head-left {
  display: flex;
  align-items: center;
  gap: 12px;
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
}
.edit-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 19px;
  font-weight: 600;
  margin: 0;
}
.edit-sub {
  font-size: 12.5px;
  color: var(--ink-faint);
  margin: 2px 0 0;
}
.head-actions {
  display: flex;
  gap: 10px;
}

.step {
  padding: 20px 22px;
}
.step-head {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}
.step-head-main {
  flex: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
}
.step-no {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: var(--brand);
  color: #fff;
  font-family: 'Space Grotesk', sans-serif;
  font-weight: 700;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.step-no.muted-no {
  background: var(--panel-alt);
  color: var(--ink-faint);
  border: 1px solid var(--border);
}
.step-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 600;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}
.step-hint {
  font-size: 12.5px;
  color: var(--ink-faint);
  margin: 3px 0 0;
}

.gen-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 10px 12px;
  background: var(--panel-alt);
  border: 1px solid var(--border);
  border-radius: 8px;
  font-size: 12.5px;
  color: var(--ink-soft);
}
.gen-tip .el-icon {
  color: var(--brand);
}
.gen-action {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}
.gen-action-hint {
  font-size: 12px;
  color: var(--ink-faint);
}

.mode-bar {
  margin-bottom: 14px;
}
.adv-title {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13.5px;
  font-weight: 500;
}
.adv-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--brand);
}
</style>
