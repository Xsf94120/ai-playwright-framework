<template>
  <el-dialog
    :model-value="modelValue"
    title="发起测试运行"
    width="540"
    @update:model-value="$emit('update:modelValue', $event)"
    @open="onOpen"
  >
    <el-form :model="form" label-position="top">
      <div class="form-grid">
        <el-form-item label="项目">
          <el-select
            v-model="form.project_id"
            style="width: 100%"
            :disabled="lockProject"
            @change="onProjectChange"
          >
            <el-option
              v-for="p in projects"
              :key="p.id"
              :label="`${p.name} (${p.key})`"
              :value="p.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="用例集">
          <el-select
            v-model="form.suite_name"
            clearable
            placeholder="留空运行全部用例集"
            style="width: 100%"
          >
            <el-option v-for="s in suites" :key="s.id" :label="s.name" :value="s.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境">
          <el-select v-model="form.env" style="width: 100%">
            <el-option v-for="e in envOptions" :key="e.name" :label="envLabel(e)" :value="e.name" />
          </el-select>
        </el-form-item>
        <el-form-item label="浏览器">
          <el-select v-model="form.browser" style="width: 100%">
            <el-option label="chromium" value="chromium" />
            <el-option label="firefox" value="firefox" />
            <el-option label="webkit" value="webkit" />
          </el-select>
        </el-form-item>
      </div>
      <el-form-item label="AI 定位模式">
        <el-radio-group v-model="form.ai_mode">
          <el-radio-button value="strict">strict 严格</el-radio-button>
          <el-radio-button value="assist">assist 辅助</el-radio-button>
          <el-radio-button value="off">off 关闭</el-radio-button>
        </el-radio-group>
      </el-form-item>
      <el-alert
        v-if="selectedEnvMissingUrl"
        type="warning"
        :closable="false"
        show-icon
        title="所选环境尚未配置 BASE_URL，运行会失败。请先到「设置 / 环境」补全。"
      />
    </el-form>
    <template #footer>
      <el-button @click="$emit('update:modelValue', false)">取消</el-button>
      <el-button
        type="primary"
        :icon="VideoPlay"
        :loading="submitting"
        :disabled="!form.project_id"
        @click="submit"
      >
        开始运行
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { VideoPlay } from '@element-plus/icons-vue'
import api from '../api/client'

const props = defineProps({
  modelValue: { type: Boolean, default: false },
  // 预设项目（工作区内打开时锁定）
  presetProjectId: { type: [Number, String], default: null },
  presetSuiteName: { type: String, default: '' },
  lockProject: { type: Boolean, default: false },
})
const emit = defineEmits(['update:modelValue', 'submitted'])
const router = useRouter()

const projects = ref([])
const suites = ref([])
const submitting = ref(false)

const form = reactive({
  project_id: null,
  suite_name: '',
  env: '',
  ai_mode: 'strict',
  browser: 'chromium',
})

const currentProject = computed(() =>
  projects.value.find((p) => p.id === form.project_id)
)
const envOptions = computed(() => currentProject.value?.environments || [])
const selectedEnvMissingUrl = computed(() => {
  const e = envOptions.value.find((x) => x.name === form.env)
  return e ? !(e.base_url || '').trim() : false
})

function envLabel(e) {
  return (e.base_url || '').trim() ? e.name : `${e.name} (未配置URL)`
}

async function onOpen() {
  if (!projects.value.length) {
    const { data } = await api.get('/projects')
    projects.value = data
  }
  const preset = props.presetProjectId
    ? Number(props.presetProjectId)
    : projects.value[0]?.id
  form.project_id = preset || null
  form.suite_name = props.presetSuiteName || ''
  if (preset) await loadSuites(preset)
  pickDefaultEnv()
}

async function loadSuites(projectId) {
  if (!projectId) {
    suites.value = []
    return
  }
  const { data } = await api.get(`/projects/${projectId}/suites`)
  suites.value = data
}

function pickDefaultEnv() {
  const envs = envOptions.value
  if (!envs.length) {
    form.env = ''
    return
  }
  // 优先选已配置 URL 的环境
  const ready = envs.find((e) => (e.base_url || '').trim())
  form.env = (ready || envs[0]).name
}

async function onProjectChange(id) {
  form.suite_name = ''
  await loadSuites(id)
  pickDefaultEnv()
}

async function submit() {
  if (!form.project_id) {
    ElMessage.warning('请选择项目')
    return
  }
  submitting.value = true
  try {
    const { data } = await api.post('/runs', { ...form })
    emit('update:modelValue', false)
    emit('submitted', data)
    router.push({
      name: 'project-run-detail',
      params: { id: form.project_id, runId: data.id },
    })
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 0 16px;
}
</style>
