<template>
  <div>
    <el-alert
      type="success"
      :closable="false"
      class="mb"
      title="用自然语言描述测试步骤，平台将驱动 AI 生成可执行用例（对应 generation 层）。"
    />

    <div v-for="(c, ci) in cases" :key="ci" class="case-card">
      <div class="case-head">
        <el-input v-model="c.name" placeholder="用例名称，如：login_success" class="case-name mono" />
        <el-button :icon="Delete" text type="danger" @click="cases.splice(ci, 1)">删除用例</el-button>
      </div>

      <el-input
        v-model="c.description"
        placeholder="用例描述（可选）"
        class="mb-s"
      />

      <div class="field-label">测试步骤（自然语言，每行一步）</div>
      <div v-for="(_, si) in c.steps" :key="si" class="line-row">
        <span class="line-no">{{ si + 1 }}</span>
        <el-input
          v-model="c.steps[si]"
          placeholder="如：在用户名输入框输入 standard_user"
          @keyup.enter="addStep(c, si)"
        />
        <el-button :icon="Delete" text @click="c.steps.splice(si, 1)" />
      </div>
      <el-button size="small" :icon="Plus" text type="primary" @click="addStep(c)">
        添加步骤
      </el-button>

      <div class="field-label">校验点（可选）</div>
      <div v-for="(_, ki) in c.checkpoints" :key="ki" class="line-row">
        <span class="line-no">✓</span>
        <el-input
          v-model="c.checkpoints[ki]"
          placeholder="如：页面应跳转到商品列表页"
        />
        <el-button :icon="Delete" text @click="c.checkpoints.splice(ki, 1)" />
      </div>
      <el-button size="small" :icon="Plus" text type="primary" @click="c.checkpoints.push('')">
        添加校验点
      </el-button>

      <div class="field-label">收尾动作 final（可选）</div>
      <el-input v-model="c.final" placeholder="如：点击退出登录" class="mb-s" />
    </div>

    <el-button :icon="Plus" @click="addCase" class="add-case">添加用例</el-button>
  </div>
</template>

<script setup>
import { Plus, Delete } from '@element-plus/icons-vue'

const cases = defineModel({ type: Array, default: () => [] })

function addCase() {
  cases.value.push({
    name: '',
    description: '',
    steps: [''],
    checkpoints: [],
    final: '',
  })
}

function addStep(c, index) {
  if (index === undefined) c.steps.push('')
  else c.steps.splice(index + 1, 0, '')
}
</script>

<style scoped>
.case-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 16px;
  margin-bottom: 16px;
  background: var(--panel-alt);
}
.case-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 10px;
}
.case-name {
  max-width: 320px;
}
.field-label {
  font-size: 12.5px;
  font-weight: 600;
  color: var(--ink-soft);
  margin: 14px 0 8px;
}
.line-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}
.line-no {
  width: 22px;
  height: 22px;
  flex-shrink: 0;
  border-radius: 6px;
  background: var(--brand-soft);
  color: var(--brand-strong);
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.mb {
  margin-bottom: 16px;
}
.mb-s {
  margin-bottom: 8px;
}
.add-case {
  width: 100%;
}
</style>
