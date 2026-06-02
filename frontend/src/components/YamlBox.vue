<template>
  <div>
    <el-input
      v-model="model"
      type="textarea"
      :rows="rows"
      class="mono yaml-box"
      :placeholder="placeholder"
      spellcheck="false"
    />
    <div class="status" :class="{ err: !!error }">
      <span v-if="error">YAML 错误：{{ error }}</span>
      <span v-else class="muted">YAML 语法正确</span>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { safeParse } from '../utils/yaml'

const props = defineProps({
  rows: { type: Number, default: 18 },
  placeholder: { type: String, default: '在此输入 YAML' },
})

const model = defineModel({ type: String, default: '' })

const error = computed(() => {
  if (!model.value || !model.value.trim()) return null
  return safeParse(model.value).error
})
</script>

<style scoped>
.yaml-box :deep(textarea) {
  font-family: 'SFMono-Regular', Consolas, Menlo, monospace;
  font-size: 12.5px;
  line-height: 1.6;
}
.status {
  margin-top: 8px;
  font-size: 12px;
}
.status.err {
  color: var(--el-color-danger);
}
</style>
