<script setup lang="ts">
import { computed } from 'vue'
import type { DispatchObservation } from '../api/types'
const props = defineProps<{ items: DispatchObservation[] }>()
const points = computed(() => {
  if (!props.items.length) return ''
  const values = props.items.map((item) => Number(item.price)); const min = Math.min(...values); const max = Math.max(...values); const range = max - min || 1
  return values.map((value, index) => `${props.items.length === 1 ? 50 : 5 + (index / (props.items.length - 1)) * 90},${90 - ((value - min) / range) * 75}`).join(' ')
})
const summary = computed(() => props.items.map((item) => `${new Date(item.interval_datetime).toLocaleTimeString('en-AU')}: $${item.price} per megawatt-hour`).join('; '))
</script>
<template><figure v-if="items.length" class="chart"><svg viewBox="0 0 100 100" role="img" aria-labelledby="chart-title chart-description"><title id="chart-title">Regional price trend</title><desc id="chart-description">{{ summary }}</desc><line x1="5" y1="90" x2="95" y2="90" /><line x1="5" y1="15" x2="5" y2="90" /><polyline :points="points" /></svg></figure></template>
