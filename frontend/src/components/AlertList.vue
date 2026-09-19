<script setup lang="ts">
import { reactive } from 'vue'
import type { AlertItem } from '../api/types'
defineProps<{ alerts: AlertItem[] }>()
const emit = defineEmits<{ acknowledge: [id: string, note: string] }>()
const notes = reactive<Record<string, string>>({})
</script>
<template>
  <section class="panel" aria-labelledby="alerts-heading">
    <div class="section-heading"><div><p class="eyebrow">Rule outcomes</p><h2 id="alerts-heading">Alerts</h2></div></div>
    <ul v-if="alerts.length" class="alert-list"><li v-for="alert in alerts" :key="alert.id" class="alert-card" :data-severity="alert.severity"><div><span class="severity">{{ alert.severity }}</span><strong>{{ alert.region }} · {{ alert.rule_type.replaceAll('_', ' ') }}</strong></div><p>{{ alert.message }}</p><dl class="alert-values"><div><dt>Observed</dt><dd>{{ alert.observed_value }}</dd></div><div><dt>Threshold</dt><dd>{{ alert.threshold }}</dd></div></dl><p class="timestamp">{{ new Date(alert.created_at).toLocaleString('en-AU') }} · {{ alert.acknowledged_at ? 'Acknowledged' : 'Open' }}</p><form v-if="!alert.acknowledged_at" class="acknowledge" @submit.prevent="emit('acknowledge', alert.id, notes[alert.id])"><label :for="`note-${alert.id}`">Acknowledgement note</label><div><input :id="`note-${alert.id}`" v-model="notes[alert.id]" required maxlength="500" /><button type="submit">Acknowledge</button></div></form><p v-else-if="alert.acknowledgement_note" class="acknowledged-note">{{ alert.acknowledgement_note }}</p></li></ul>
    <p v-else class="empty-panel">No alerts have been raised.</p>
  </section>
</template>
