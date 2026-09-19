<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { RegionCode, RegionInfo, ReplayJob } from '../api/types'

const props = defineProps<{ regions: RegionInfo[]; job: ReplayJob | null; error: string | null }>()
const emit = defineEmits<{ start: [regions: RegionCode[], speed: number]; cancel: [] }>()
const selected = ref<RegionCode[]>([])
const speed = ref(100)
watch(() => props.regions, (regions) => {
  if (!selected.value.length) selected.value = regions.map((region) => region.code)
}, { immediate: true })
const active = computed(() => props.job && ['pending', 'running'].includes(props.job.status))
const progress = computed(() => props.job?.total ? Math.round((props.job.processed / props.job.total) * 100) : 0)
</script>
<template>
  <section class="panel replay-panel" aria-labelledby="replay-heading">
    <div class="section-heading"><div><p class="eyebrow">Repeatable demonstration</p><h2 id="replay-heading">Historical replay</h2></div></div>
    <form class="replay-form" @submit.prevent="emit('start', selected, speed)">
      <fieldset><legend>Regions</legend><label v-for="region in regions" :key="region.code"><input v-model="selected" type="checkbox" :value="region.code" /> {{ region.code }}</label></fieldset>
      <label>Replay speed<input v-model.number="speed" type="number" min="0.1" max="1000" step="0.1" required /></label>
      <button type="submit" :disabled="Boolean(active) || !selected.length">Start replay</button>
      <button v-if="active" type="button" class="button-secondary" @click="emit('cancel')">Cancel replay</button>
    </form>
    <p v-if="error" role="alert" class="form-error">{{ error }}</p>
    <div v-if="job" class="replay-progress" aria-live="polite">
      <div><strong>{{ job.status }}</strong><span>{{ job.processed }} / {{ job.total }} published · {{ job.rejected }} rejected</span></div>
      <progress :value="job.processed" :max="job.total || 1">{{ progress }}%</progress>
      <p v-if="job.current_interval" class="timestamp">Current source interval {{ new Date(job.current_interval).toLocaleString('en-AU') }}</p>
    </div>
  </section>
</template>
