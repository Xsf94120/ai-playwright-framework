<template>
  <div>
    <div class="page-header">
      <div>
        <h2 class="page-title">项目管理</h2>
        <p class="page-subtitle">每个项目对应一套测试环境、LLM 配置与用例集</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建项目</el-button>
    </div>

    <div class="panel" v-loading="loading">
      <el-table :data="projects" stripe>
        <el-table-column label="项目" min-width="220">
          <template #default="{ row }">
            <div class="proj-cell" @click="goDetail(row)">
              <span class="proj-name">{{ row.name }}</span>
              <el-tag size="small" type="info" class="mono">{{ row.key }}</el-tag>
            </div>
            <div class="muted proj-desc">{{ row.description || '暂无描述' }}</div>
          </template>
        </el-table-column>
        <el-table-column label="环境" width="220">
          <template #default="{ row }">
            <el-tag
              v-for="env in row.environments"
              :key="env.id"
              size="small"
              class="env-tag"
            >
              {{ env.name }}
            </el-tag>
            <span v-if="!row.environments.length" class="muted">未配置</span>
          </template>
        </el-table-column>
        <el-table-column label="视口" width="130">
          <template #default="{ row }">
            <span class="mono">{{ row.viewport_width }}×{{ row.viewport_height }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="220" align="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="goDetail(row)">配置</el-button>
            <el-button text type="primary" @click="goRuns(row)">执行</el-button>
            <el-button text type="danger" @click="remove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="dialogVisible" title="新建项目" width="560">
      <el-form ref="formRef" :model="form" :rules="rules" label-width="96px">
        <el-form-item label="项目名称" prop="name">
          <el-input v-model="form.name" placeholder="如：电商后台" />
        </el-form-item>
        <el-form-item label="项目标识" prop="key">
          <el-input v-model="form.key" placeholder="小写字母/数字/下划线，如：shop_admin" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item label="视口">
          <div class="flex gap-8">
            <el-input-number v-model="form.viewport_width" :min="320" :max="3840" />
            <span class="muted">×</span>
            <el-input-number v-model="form.viewport_height" :min="320" :max="2160" />
          </div>
        </el-form-item>
        <el-form-item label="Tracing">
          <el-select v-model="form.tracing" style="width: 200px">
            <el-option label="off 关闭" value="off" />
            <el-option label="on 始终录制" value="on" />
            <el-option label="retain-on-failure 失败保留" value="retain-on-failure" />
          </el-select>
        </el-form-item>
        <el-form-item label="环境地址">
          <div class="env-editor">
            <div v-for="(env, i) in form.environments" :key="i" class="env-row">
              <el-input v-model="env.name" placeholder="环境名" style="width: 110px" />
              <el-input v-model="env.base_url" placeholder="https://..." />
              <el-button :icon="Delete" text @click="form.environments.splice(i, 1)" />
            </div>
            <el-button size="small" :icon="Plus" @click="addEnv">添加环境</el-button>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="submit">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Delete } from '@element-plus/icons-vue'
import api from '../api/client'

const router = useRouter()
const projects = ref([])
const loading = ref(false)
const dialogVisible = ref(false)
const saving = ref(false)
const formRef = ref()

const form = reactive({
  name: '',
  key: '',
  description: '',
  viewport_width: 1280,
  viewport_height: 720,
  tracing: 'off',
  environments: [{ name: 'prod', base_url: '' }],
})

const rules = {
  name: [{ required: true, message: '请输入项目名称', trigger: 'blur' }],
  key: [
    { required: true, message: '请输入项目标识', trigger: 'blur' },
    {
      pattern: /^[a-z][a-z0-9_]*$/,
      message: '只能包含小写字母、数字和下划线，且以字母开头',
      trigger: 'blur',
    },
  ],
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get('/projects')
    projects.value = data
  } finally {
    loading.value = false
  }
}

function openCreate() {
  Object.assign(form, {
    name: '',
    key: '',
    description: '',
    viewport_width: 1280,
    viewport_height: 720,
    tracing: 'off',
    environments: [{ name: 'prod', base_url: '' }],
  })
  dialogVisible.value = true
}

function addEnv() {
  form.environments.push({ name: '', base_url: '' })
}

async function submit() {
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    saving.value = true
    try {
      const payload = {
        ...form,
        environments: form.environments.filter((e) => e.name.trim()),
      }
      const { data } = await api.post('/projects', payload)
      ElMessage.success('项目已创建')
      dialogVisible.value = false
      await load()
      router.push({ name: 'project-detail', params: { id: data.id } })
    } finally {
      saving.value = false
    }
  })
}

function goDetail(row) {
  router.push({ name: 'project-detail', params: { id: row.id } })
}

function goRuns(row) {
  router.push({ name: 'runs', query: { project: row.id } })
}

async function remove(row) {
  await ElMessageBox.confirm(
    `确定删除项目「${row.name}」及其所有用例集与运行记录吗？`,
    '删除确认',
    { type: 'warning', confirmButtonText: '删除', cancelButtonText: '取消' }
  )
  await api.delete(`/projects/${row.id}`)
  ElMessage.success('已删除')
  await load()
}

onMounted(load)
</script>

<style scoped>
.proj-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}
.proj-name {
  font-weight: 600;
}
.proj-desc {
  font-size: 12.5px;
  margin-top: 2px;
}
.env-tag {
  margin-right: 6px;
}
.env-editor {
  width: 100%;
}
.env-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
</style>
