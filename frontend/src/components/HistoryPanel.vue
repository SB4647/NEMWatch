<script setup lang="ts">
import { ref } from 'vue'
import type { DispatchObservation, RegionCode, RegionInfo } from '../api/types'
import HistoryChart from './HistoryChart.vue'
defineProps<{ regions: RegionInfo[]; items: DispatchObservation[]; selectedRegion: RegionCode; loading: boolean }>()
const emit = defineEmits<{ 'update:selectedRegion': [value: RegionCode]; load: [start: string, end: string] }>()
const start = ref('2026-09-19T00:00'); const end = ref('2026-09-19T00:15')
</script>
<template>
  <section class="panel" aria-labelledby="history-heading">
    <div class="section-heading"><div><p class="eyebrow">Explore intervals</p><h2 id="history-heading">Market history</h2></div></div>
    <form class="filters" @submit.prevent="emit('load', start, end)">
      <label>Region<select :value="selectedRegion" @change="emit('update:selectedRegion', ($event.target as HTMLSelectElement).value as RegionCode)"><option v-for="region in regions" :key="region.code" :value="region.code">{{ region.name }}</option></select></label>
      <label>Start (UTC)<input v-model="start" type="datetime-local" required /></label><label>End (UTC)<input v-model="end" type="datetime-local" required /></label>
      <button type="submit" :disabled="loading">{{ loading ? 'Loading…' : 'Load history' }}</button>
    </form>
    <template v-if="items.length">
      <HistoryChart :items="items" />
      <div class="table-wrap"><table><caption>Price and demand values shown in the trend chart</caption><thead><tr><th scope="col">Interval</th><th scope="col">Price ($/MWh)</th><th scope="col">Demand (MW)</th></tr></thead><tbody><tr v-for="item in items" :key="item.interval_datetime"><td>{{ new Date(item.interval_datetime).toLocaleString('en-AU') }}</td><td>{{ item.price }}</td><td>{{ item.demand }}</td></tr></tbody></table></div>
    </template>
    <p v-else class="empty-panel">Choose a region and UTC range to view observations.</p>
  </section>
</template>
