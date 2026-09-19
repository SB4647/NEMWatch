import { computed, onMounted, ref } from 'vue'

import { ApiError, type NemWatchClient } from '../api/client'
import type { AlertItem, DispatchObservation, RegionCode, RegionInfo } from '../api/types'

export function useMarketDashboard(client: NemWatchClient) {
  const regions = ref<RegionInfo[]>([])
  const latest = ref<DispatchObservation[]>([])
  const history = ref<DispatchObservation[]>([])
  const alerts = ref<AlertItem[]>([])
  const selectedRegion = ref<RegionCode>('QLD1')
  const loading = ref(true)
  const historyLoading = ref(false)
  const error = ref<string | null>(null)
  const announcement = ref('')
  let historyToken = 0

  const latestByRegion = computed(() => new Map(latest.value.map((item) => [item.region, item])))

  async function refresh(): Promise<void> {
    loading.value = true
    error.value = null
    try {
      const [regionData, latestData, alertPage] = await Promise.all([
        client.getRegions(), client.getLatest(), client.getAlerts(),
      ])
      regions.value = regionData
      latest.value = latestData
      alerts.value = alertPage.items
      announcement.value = 'Market overview updated.'
    } catch (caught) {
      error.value = caught instanceof ApiError ? caught.message : 'NEMWatch could not load market data.'
    } finally {
      loading.value = false
    }
  }

  async function loadHistory(start: string, end: string): Promise<void> {
    const token = ++historyToken
    historyLoading.value = true
    error.value = null
    try {
      const page = await client.getHistory(selectedRegion.value, `${start}:00Z`, `${end}:00Z`)
      if (token === historyToken) history.value = page.items
    } catch (caught) {
      if (token === historyToken) error.value = caught instanceof ApiError ? caught.message : 'History could not be loaded.'
    } finally {
      if (token === historyToken) historyLoading.value = false
    }
  }

  onMounted(refresh)
  return { regions, latest, latestByRegion, history, alerts, selectedRegion, loading, historyLoading, error, announcement, refresh, loadHistory }
}
