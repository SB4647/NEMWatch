<script setup lang="ts">
import type { DispatchObservation, RegionCode, RegionInfo } from '../api/types'
defineProps<{ regions: RegionInfo[]; latestByRegion: Map<RegionCode, DispatchObservation> }>()
function number(value: string | null, maximumFractionDigits = 1): string {
  return value === null ? 'Unavailable' : new Intl.NumberFormat('en-AU', { maximumFractionDigits }).format(Number(value))
}
function freshness(item?: DispatchObservation): 'fresh' | 'stale' | 'missing' {
  if (!item) return 'missing'
  return Date.now() - Date.parse(item.interval_datetime) <= 15 * 60 * 1000 ? 'fresh' : 'stale'
}
</script>
<template>
  <section aria-labelledby="overview-heading">
    <div class="section-heading"><div><p class="eyebrow">Five NEM regions</p><h2 id="overview-heading">Regional overview</h2></div></div>
    <div v-if="regions.length" class="region-grid">
      <article v-for="region in regions" :key="region.code" class="region-card" :data-state="freshness(latestByRegion.get(region.code))" :aria-labelledby="`region-${region.code}`">
        <div class="region-card__header"><div><p class="region-code">{{ region.code }}</p><h3 :id="`region-${region.code}`">{{ region.name }}</h3></div><span class="freshness">{{ freshness(latestByRegion.get(region.code)) }}</span></div>
        <template v-if="latestByRegion.get(region.code)">
          <p class="price" data-testid="market-value"><span>${{ number(latestByRegion.get(region.code)!.price, 2) }}</span><small>/MWh</small></p>
          <dl class="metrics"><div><dt>Demand</dt><dd>{{ number(latestByRegion.get(region.code)!.demand) }} MW</dd></div><div><dt>Generation</dt><dd>{{ number(latestByRegion.get(region.code)!.generation) }} MW</dd></div><div><dt>Interchange</dt><dd>{{ number(latestByRegion.get(region.code)!.interchange) }} MW</dd></div></dl>
          <p class="timestamp">Interval {{ new Date(latestByRegion.get(region.code)!.interval_datetime).toLocaleString('en-AU') }}</p>
        </template>
        <p v-else class="empty-copy">No observation has been received.</p>
      </article>
    </div>
    <p v-else class="empty-panel">No regional data is available yet. Load the fixture to begin.</p>
  </section>
</template>
