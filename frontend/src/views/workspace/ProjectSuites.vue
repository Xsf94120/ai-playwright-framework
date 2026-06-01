<template>
  <div v-loading="loading">
    <div class="list-head">
      <span class="muted">
        用例集由分层 YAML 组成（步骤描述 / 元素 / 数据 / 模块 / 变量），AI 可据此生成可执行用例
      </span>
      <el-button type="primary" :icon="Plus" @click="goNew">新建用例集</el-button>
    </div>

    <div v-if="suites.length" class="suite-grid">
      <article
        v-for="s in suites"
        :key="s.id"
        class="suite-card"
        @click="edit(s)"
      >
        <div class="card-top">
          <div class="card-icon"><el-icon><Document /></el-icon></div>
          <el-dropdown trigger="click" @command="(c) => onCommand(c, s)" @click.stop>
            <button class="more-btn" @click.stop><el-icon><MoreFilled /></el-icon></button>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="edit" :icon="Edit">编辑</el-dropdown-item>
                <el-dropdown-item command="run" :icon="VideoPlay">运行</el-dropdown-item>
                <el-dropdown-item command="delete" :icon="Delete" divided>删除</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
        <h3 class="suite-name mono">{{ s.name }}</h3>
        <p class="suite-desc">{{ s.description || '暂无描述' }}</p>
        <div class="suite-layers">
          <span v-for="l in layerTags(s)" :key="l" class="layer-chip mono">{{ l }}</span>
          <span v-if="!layerTags(s).length" class="layer-empty">空用例集</span>
        </div>
        <div class="card-actions" @click.stop>
          <el-button size="small" :icon="VideoPlay" @click="run(s)">运行</el-button>
          <el-button size="small" type="primary" :icon="Edit" @click="edit(s)">编辑</el-button>
        </div>
      </article>
    </div>

    <div v-else-if="!loading" class="empty-state">
      <el-icon class="empty-icon"><FolderOpened /></el-icon>
      <h3>还没有用例集</h3>
      <p>创建第一个用例集，用自然语言描述测试步骤并由 AI 生成可执行用例</p>
      <el-button type="primary" :icon="Plus" @click="goNew">新建用例集</el-button>
    </div>

    <RunDialog
      v-model="runVisible"
      :preset-project-id="projectId"
      :preset-suite-name="runSuiteName"
      lock-project
    />
  </div>
</template>

<script setup>
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Plus,
  Document,
  MoreFilled,
  Edit,
  Delete,
  VideoPlay,
  FolderOpened,
} from '@element-plus/icons-vue'
import api from '../../api/client'
import RunDialog from '../../components/RunDialog.vue'

const route = useRoute()
const router = useRouter()
const projectId = route.params.id

const suites = ref([])
const loading = ref(false)
const runVisible = ref(false)
const runSuiteName = ref('')

const LAYER_MAP = {
  generation_yaml: '步骤',
  elements_yaml: '元素',
  cases_yaml: 'cases',
  data_yaml: '数据',
  modules_yaml: '模块',
  vars_yaml: '变量',
}

function layerTags(s) {
  return Object.entries(LAYER_MAP)
    .filter(([k]) => (s[k] || '').trim())
    .map(([, v]) => v)
}

async function load() {
  loading.value = true
  try {
    const { data } = await api.get(`/projects/${projectId}/suites`)
    suites.value = data
  } finally {
    loading.value = false
  }
}

function goNew() {
  router.push({ name: 'suite-new', params: { id: projectId } })
}
function edit(s) {
  router.push({ name: 'suite-edit', params: { id: projectId, suiteId: s.id } })
}
function run(s) {
  runSuiteName.value = s.name
  runVisible.value = true
}
async function remove(s) {
  await ElMessageBox.confirm(`确定删除用例集「${s.name}」吗？此操作不可撤销。`, '删除确认', {
    type: 'warning',
    confirmButtonText: '删除',
    cancelButtonText: '取消',
  })
  await api.delete(`/projects/${projectId}/suites/${s.id}`)
  ElMessage.success('已删除')
  await load()
}
function onCommand(cmd, s) {
  if (cmd === 'edit') edit(s)
  else if (cmd === 'run') run(s)
  else if (cmd === 'delete') remove(s)
}

onMounted(load)
</script>

<style scoped>
.list-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}

.suite-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(290px, 1fr));
  gap: 14px;
}
.suite-card {
  background: var(--panel);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px;
  cursor: pointer;
  display: flex;
  flex-direction: column;
  transition: box-shadow 0.16s, transform 0.16s, border-color 0.16s;
  position: relative;
}
.suite-card:hover {
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
  border-color: var(--border-strong);
}
.card-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 12px;
}
.card-icon {
  width: 38px;
  height: 38px;
  border-radius: 9px;
  background: var(--brand-soft);
  color: var(--brand);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
}
.more-btn {
  border: none;
  background: none;
  color: var(--ink-faint);
  cursor: pointer;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.more-btn:hover {
  background: var(--panel-tint);
  color: var(--ink);
}
.suite-name {
  font-size: 15px;
  font-weight: 600;
  margin: 0 0 4px;
  color: var(--ink);
}
.suite-desc {
  font-size: 12.5px;
  color: var(--ink-faint);
  margin: 0 0 14px;
  line-height: 1.5;
  min-height: 19px;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.suite-layers {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 16px;
  min-height: 22px;
}
.layer-chip {
  font-size: 10.5px;
  color: var(--ink-soft);
  background: var(--panel-alt);
  border: 1px solid var(--border);
  padding: 2px 7px;
  border-radius: 5px;
}
.layer-empty {
  font-size: 11.5px;
  color: var(--ink-faint);
}
.card-actions {
  display: flex;
  gap: 8px;
  margin-top: auto;
  padding-top: 4px;
}
.card-actions .el-button {
  flex: 1;
}

.empty-state {
  text-align: center;
  padding: 70px 20px;
  background: var(--panel);
  border: 1px dashed var(--border-strong);
  border-radius: var(--radius);
}
.empty-icon {
  font-size: 44px;
  color: var(--ink-faint);
  margin-bottom: 14px;
}
.empty-state h3 {
  font-family: 'Space Grotesk', sans-serif;
  font-size: 17px;
  margin: 0 0 6px;
}
.empty-state p {
  color: var(--ink-faint);
  font-size: 13.5px;
  margin: 0 0 18px;
  max-width: 380px;
  margin-left: auto;
  margin-right: auto;
}
</style>
