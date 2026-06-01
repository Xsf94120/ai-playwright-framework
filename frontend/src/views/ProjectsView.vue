<template>
  <div>
    <div class="page-header">
      <div>
        <p class="kicker">PROJECTS</p>
        <h2 class="page-title">项目管理</h2>
        <p class="page-subtitle">每个项目对应一套测试环境、LLM 配置与用例集</p>
      </div>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建项目</el-button>
    </div>

    <div v-loading="loading">
      <div v-if="projects.length" class="proj-grid">
        <article
          v-for="p in projects"
          :key="p.id"
          class="proj-card"
          @click="goDetail(p)"
        >
          <div class="card-top">
            <div class="card-avatar">{{ p.name.charAt(0).toUpperCase() }}</div>
            <el-dropdown trigger="click" @command="(c) => onCommand(c, p)" @click.stop>
              <el-button text :icon="MoreFilled" class="more-btn" @click.stop />
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="config" :icon="Setting">配置</el-dropdown-item>
                  <el-dropdown-item command="run" :icon="VideoPlay">执行</el-dropdown-item>
                  <el-dropdown-item command="delete" :icon="Delete" divided>删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>

          <h3 class="card-name">{{ p.name }}</h3>
          <span class="badge neutral mono card-key">{{ p.key }}</span>
          <p class="card-desc">{{ p.description || '暂无描述' }}</p>

          <div class="card-envs">
            <span v-for="env in p.environments" :key="env.id" class="env-chip">
              <span class="env-dot" />{{ env.name }}
            </span>
            <span v-if="!p.environments.length" class="muted" style="font-size: 12px">
              未配置环境
            </span>
          </div>

          <div class="card-foot">
            <span class="mono">{{ p.viewport_width }}×{{ p.viewport_height }}</span>
            <span class="trace-tag" :class="{ on: p.tracing !== 'off' }">
              Tracing {{ p.tracing }}
            </span>
          </div>
        </article>
      </div>

      <div v-else-if="!loading" class="empty-state">
        <div class="empty-icon"><el-icon><FolderOpened /></el-icon></div>
        <h3>还没有项目</h3>
        <p class="muted">创建第一个项目，开始配置环境、用例集与 AI 运行参数</p>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建项目</el-button>
      </div>
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
          <el-select v-model="form.tracing" style="width: 220px">
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
import {
  Plus,
  Delete,
  MoreFilled,
  Setting,
  VideoPlay,
  FolderOpened,
} from '@element-plus/icons-vue'
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
      router.push({ name: 'project-overview', params: { id: data.id } })
    } finally {
      saving.value = false
    }
  })
}

function goDetail(row) {
  router.push({ name: 'project-overview', params: { id: row.id } })
}

function onCommand(command, row) {
  if (command === 'config') goDetail(row)
  else if (command === 'run') router.push({ name: 'runs', query: { project: row.id } })
  else if (command === 'delete') remove(row)
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
.proj-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 14px;
}

.proj-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  cursor: pointer;
  box-shadow: var(--shadow-sm);
  transition: box-shadow 0.18s, transform 0.18s, border-color 0.18s;
  display: flex;
  flex-direction: column;
  position: relative;
}
.proj-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 16px;
  bottom: 16px;
  width: 3px;
  background: var(--brand);
  border-radius: 0 3px 3px 0;
  opacity: 0;
  transition: opacity 0.18s;
}
.proj-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--border-strong);
}
.proj-card:hover::before {
  opacity: 1;
}

.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.card-avatar {
  width: 40px;
  height: 40px;
  border-radius: 9px;
  background: var(--void);
  color: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 17px;
  font-family: 'Space Grotesk', sans-serif;
}

.more-btn {
  color: var(--ink-faint);
  padding: 4px;
}

.card-name {
  font-size: 16px;
  font-weight: 650;
  letter-spacing: -0.01em;
  margin: 14px 0 8px;
}

.card-key {
  align-self: flex-start;
}

.card-desc {
  font-size: 13px;
  color: var(--ink-soft);
  margin: 12px 0 14px;
  line-height: 1.55;
  min-height: 40px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.card-envs {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
  margin-bottom: 16px;
}

.env-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 550;
  padding: 3px 10px;
  border-radius: 999px;
  background: var(--panel-alt);
  border: 1px solid var(--border);
  color: var(--ink-soft);
}
.env-chip .env-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--brand);
}

.card-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-top: 1px solid var(--border);
  padding-top: 14px;
  margin-top: auto;
  font-size: 12px;
  color: var(--ink-soft);
}

.trace-tag {
  font-size: 11px;
  font-weight: 600;
  color: var(--ink-faint);
}
.trace-tag.on {
  color: var(--warn);
}

.empty-state {
  text-align: center;
  padding: 70px 20px;
  background: var(--panel);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius);
}
.empty-icon {
  width: 60px;
  height: 60px;
  border-radius: 16px;
  background: var(--brand-soft);
  color: var(--brand);
  font-size: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 16px;
}
.empty-state h3 {
  margin: 0 0 6px;
  font-size: 17px;
}
.empty-state p {
  margin: 0 0 18px;
  font-size: 13px;
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
