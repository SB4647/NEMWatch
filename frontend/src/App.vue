<script setup lang="ts">
import { api } from './api/client'
import AlertList from './components/AlertList.vue'
import HistoryPanel from './components/HistoryPanel.vue'
import LiveStatus from './components/LiveStatus.vue'
import RegionOverview from './components/RegionOverview.vue'
import ReplayControl from './components/ReplayControl.vue'
import StatusBanner from './components/StatusBanner.vue'
import { useMarketDashboard } from './composables/useMarketDashboard'

const dashboard = useMarketDashboard(api)
</script>

<template>
  <main class="shell">
    <header class="hero" aria-labelledby="page-title">
      <div><p class="eyebrow">National Electricity Market monitor</p><h1 id="page-title">NEMWatch</h1><p class="summary">Regional prices, demand, event-driven alerts, and repeatable historical playback.</p><LiveStatus :state="dashboard.connectionState.value" /></div>
      <p class="disclaimer">Educational use only. Not a trading, dispatch, or operational control system. Fixture values are not current market information.</p>
    </header>
    <StatusBanner :loading="dashboard.loading.value" :error="dashboard.error.value" @retry="dashboard.refresh" />
    <RegionOverview :regions="dashboard.regions.value" :latest-by-region="dashboard.latestByRegion.value" />
    <div class="content-grid">
      <HistoryPanel v-model:selected-region="dashboard.selectedRegion.value" :regions="dashboard.regions.value" :items="dashboard.history.value" :loading="dashboard.historyLoading.value" @load="dashboard.loadHistory" />
      <AlertList :alerts="dashboard.alerts.value" @acknowledge="dashboard.acknowledgeAlert" />
    </div>
    <ReplayControl :regions="dashboard.regions.value" :job="dashboard.replay.value" :error="dashboard.replayError.value" @start="dashboard.startReplay" @cancel="dashboard.cancelReplay" />
    <p class="sr-only" aria-live="polite">{{ dashboard.announcement.value }}</p>
  </main>
</template>
