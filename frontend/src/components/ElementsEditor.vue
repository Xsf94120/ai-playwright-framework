<template>
  <div>
    <el-alert
      type="info"
      :closable="false"
      class="mb"
      title="维护页面元素定位（名称 → 选择器），供用例步骤引用（对应 elements 层）。"
    />
    <el-table :data="rows" border size="small">
      <el-table-column label="元素名称" width="260">
        <template #default="{ row }">
          <el-input v-model="row.name" placeholder="如：username_input" class="mono" />
        </template>
      </el-table-column>
      <el-table-column label="选择器 / 定位">
        <template #default="{ row }">
          <el-input v-model="row.selector" placeholder="如：#user-name 或 text=登录" class="mono" />
        </template>
      </el-table-column>
      <el-table-column width="70" align="center">
        <template #default="{ $index }">
          <el-button :icon="Delete" text type="danger" @click="rows.splice($index, 1)" />
        </template>
      </el-table-column>
    </el-table>
    <el-button size="small" :icon="Plus" class="mt" @click="rows.push({ name: '', selector: '' })">
      添加元素
    </el-button>
  </div>
</template>

<script setup>
import { Plus, Delete } from '@element-plus/icons-vue'

const rows = defineModel({ type: Array, default: () => [] })
</script>

<style scoped>
.mb {
  margin-bottom: 16px;
}
.mt {
  margin-top: 12px;
}
</style>
