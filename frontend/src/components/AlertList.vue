<script setup lang="ts">
import type { AlertItem } from '../api/types'
defineProps<{ alerts: AlertItem[] }>()
</script>
<template>
  <section class="panel" aria-labelledby="alerts-heading">
    <div class="section-heading"><div><p class="eyebrow">Rule outcomes</p><h2 id="alerts-heading">Alerts</h2></div></div>
    <ul v-if="alerts.length" class="alert-list"><li v-for="alert in alerts" :key="alert.id" class="alert-card" :data-severity="alert.severity"><div><span class="severity">{{ alert.severity }}</span><strong>{{ alert.region }} · {{ alert.rule_type.replaceAll('_', ' ') }}</strong></div><p>{{ alert.message }}</p><dl class="alert-values"><div><dt>Observed</dt><dd>{{ alert.observed_value }}</dd></div><div><dt>Threshold</dt><dd>{{ alert.threshold }}</dd></div></dl><p class="timestamp">{{ new Date(alert.created_at).toLocaleString('en-AU') }} · {{ alert.acknowledged_at ? 'Acknowledged' : 'Open' }}</p></li></ul>
    <p v-else class="empty-panel">No alerts have been raised.</p>
  </section>
</template>
