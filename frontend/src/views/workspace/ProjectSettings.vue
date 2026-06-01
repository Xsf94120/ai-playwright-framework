<template>
  <div v-loading="loading" class="settings">
    <aside class="settings-nav">
      <button
        v-for="s in sections"
        :key="s.key"
        class="snav-item"
        :class="{ active: active === s.key }"
        @click="active = s.key"
      >
        <el-icon><component :is="s.icon" /></el-icon>
        <span>{{ s.label }}</span>
      </button>
    </aside>

    <div class="settings-body">
      <!-- 基本信息 / 环境 -->
      <section v-show="active === 'basic'" class="panel">
        <h3 class="sec-title">基本信息</h3>
        <el-form :model="form" label-width="100px" style="max-width: 640px">
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
            <el-select v-model="form.tracing" style="width: 260px">
              <el-option label="off 关闭" value="off" />
              <el-option label="on 始终录制" value="on" />
              <el-option label="retain-on-failure 失败保留" value="retain-on-failure" />
            </el-select>
          </el-form-item>
        </el-form>

        <h3 class="sec-title sec-title-spaced">环境地址</h3>
        <p class="sec-hint">每个环境对应一个 BASE_URL，运行时按所选环境注入。未配置 URL 的环境无法运行。</p>
        <div class="env-editor">
          <div v-for="(env, i) in form.environments" :key="i" class="env-row">
            <el-input v-model="env.name" placeholder="环境名 如 prod" style="width: 140px" class="mono" />
            <el-input v-model="env.base_url" placeholder="https://example.com" class="mono">
              <template #prefix><el-icon><Link /></el-icon></template>
            </el-input>
            <el-button :icon="Delete" text @click="form.environments.splice(i, 1)" />
          </div>
          <el-button size="small" :icon="Plus" @click="form.environments.push({ name: '', base_url: '' })">
            添加环境
          </el-button>
        </div>

        <div class="save-bar">
          <el-button type="primary" :loading="savingBasic" @click="saveBasic">保存基本信息</el-button>
        </div>
      </section>

      <!-- 模型 (LLM) -->
      <section v-show="active === 'llm'" class="panel">
        <h3 class="sec-title">模型 (LLM) 配置</h3>
        <p class="sec-hint">驱动 AI 用例生成与智能执行的大模型接口，物化为引擎运行时的 .env 变量。</p>
        <el-form :model="llm" label-width="100px" style="max-width: 640px">
          <el-form-item label="Base URL">
            <el-input v-model="llm.base_url" placeholder="https://api.openai.com/v1" class="mono" />
          </el-form-item>
          <el-form-item label="API Key">
            <el-input
              v-model="llm.api_key"
              type="password"
              show-password
              class="mono"
              :placeholder="llm.api_key_set ? '已配置（留空保持不变）' : '请输入 API Key'"
            />
          </el-form-item>
          <el-form-item label="模型名称">
            <el-input v-model="llm.model" placeholder="如 gpt-4o-mini" class="mono" />
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
        </el-form>
        <div class="save-bar">
          <el-button type="primary" :loading="savingLlm" @click="saveLlm">保存模型配置</el-button>
        </div>
      </section>

      <!-- AI 运行时 -->
      <section v-show="active === 'ai'" class="panel">
        <h3 class="sec-title">AI 运行时配置</h3>
        <p class="sec-hint">对应引擎的 config/ai_config.yaml，控制 AI 执行模式、重试与断言策略。</p>
        <YamlBox v-model="aiConfig" :rows="18" placeholder="ai 运行时 YAML 配置" />
        <div class="save-bar">
          <el-button type="primary" :loading="savingAi" @click="saveAi">保存运行时配置</el-button>
          <el-button @click="loadAi">重置</el-button>
        </div>
      </section>
    </div>
  </div>
</template>

<script setup>
import { inject, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Plus, Delete, Setting, Cpu, MagicStick, Link } from '@element-plus/icons-vue'
import api from '../../api/client'
import YamlBox from '../../components/YamlBox.vue'

const route = useRoute()
const projectId = route.params.id
const reloadProject = inject('reloadProject', null)

const loading = ref(false)
const savingBasic = ref(false)
const savingLlm = ref(false)
const savingAi = ref(false)
const active = ref('basic')

const sections = [
  { key: 'basic', label: '基本信息 / 环境', icon: Setting },
  { key: 'llm', label: '模型 (LLM)', icon: Cpu },
  { key: 'ai', label: 'AI 运行时', icon: MagicStick },
]

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

async function loadProject() {
  const { data } = await api.get(`/projects/${projectId}`)
  Object.assign(form, {
    name: data.name,
    description: data.description,
    viewport_width: data.viewport_width,
    viewport_height: data.viewport_height,
    tracing: data.tracing,
    environments: data.environments.map((e) => ({ name: e.name, base_url: e.base_url })),
  })
}
async function loadLlm() {
  const { data } = await api.get(`/projects/${projectId}/llm`)
  Object.assign(llm, data, { api_key: '' })
}
async function loadAi() {
  const { data } = await api.get(`/projects/${projectId}/ai-config`)
  aiConfig.value = data.content_yaml
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
    reloadProject && reloadProject()
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

onMounted(async () => {
  loading.value = true
  try {
    await Promise.all([loadProject(), loadLlm(), loadAi()])
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.settings {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 18px;
  align-items: start;
}
@media (max-width: 760px) {
  .settings {
    grid-template-columns: 1fr;
  }
}

.settings-nav {
  display: flex;
  flex-direction: column;
  gap: 2px;
  position: sticky;
  top: 16px;
}
.snav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 12px;
  border: none;
  background: none;
  cursor: pointer;
  border-radius: 7px;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--ink-soft);
  text-align: left;
  font-family: inherit;
  transition: background 0.14s, color 0.14s;
}
.snav-item .el-icon {
  font-size: 16px;
}
.snav-item:hover {
  background: var(--panel-tint);
  color: var(--ink);
}
.snav-item.active {
  background: var(--brand-soft);
  color: var(--brand-strong);
}

.sec-title {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 4px;
}
.sec-title-spaced {
  margin-top: 26px;
  padding-top: 22px;
  border-top: 1px solid var(--border);
}
.sec-hint {
  font-size: 12.5px;
  color: var(--ink-faint);
  margin: 0 0 16px;
  line-height: 1.5;
}

.env-editor {
  max-width: 640px;
}
.env-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.save-bar {
  display: flex;
  gap: 10px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
}
</style>
