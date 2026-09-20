import { computed, onBeforeUnmount, onMounted, ref } from 'vue'

import { ApiError, apiBaseUrl, type NemWatchClient } from '../api/client'
import type { AlertItem, DispatchObservation, RegionCode, RegionInfo, ReplayJob } from '../api/types'
import { MarketSocket, marketWebSocketUrl, type ConnectionState, type MarketMessage } from '../api/live'

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
  const connectionState = ref<ConnectionState>('disconnected')
  const replay = ref<ReplayJob | null>(null)
  const replayError = ref<string | null>(null)
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

  async function acknowledgeAlert(id: string, note: string): Promise<void> {
    const updated = await client.acknowledgeAlert(id, note)
    alerts.value = alerts.value.map((item) => item.id === id ? updated : item)
    announcement.value = 'Alert acknowledged.'
  }

  async function startReplay(selected: RegionCode[], speed: number): Promise<void> {
    replayError.value = null
    try {
      replay.value = await client.startReplay(selected, speed)
      localStorage.setItem('nemwatch-replay-id', replay.value.id)
    } catch (caught) {
      replayError.value = caught instanceof ApiError ? caught.message : 'Replay could not be started.'
    }
  }

  async function cancelReplay(): Promise<void> {
    if (!replay.value) return
    replay.value = await client.cancelReplay(replay.value.id)
  }

  function handleMessage(message: MarketMessage): void {
    if (message.type === 'dispatch_observed') {
      latest.value = [...latest.value.filter((item) => item.region !== message.data.region), message.data]
      announcement.value = `${message.data.region} market data updated.`
    } else if (message.type === 'alert_raised') {
      alerts.value = [message.data, ...alerts.value.filter((item) => item.id !== message.data.id)]
      announcement.value = `New ${message.data.severity} alert for ${message.data.region}.`
    } else if (message.type === 'alert_acknowledged') {
      alerts.value = alerts.value.map((item) => item.id === message.data.id ? message.data : item)
    } else if (message.type === 'replay_progress') {
      replay.value = message.data
      if (['completed', 'cancelled', 'failed'].includes(message.data.status)) {
        localStorage.removeItem('nemwatch-replay-id')
      }
    }
  }

  const socket = new MarketSocket(
    marketWebSocketUrl(apiBaseUrl),
    handleMessage,
    (state) => { connectionState.value = state },
  )

  onMounted(() => {
    void refresh()
    const replayId = localStorage.getItem('nemwatch-replay-id')
    if (replayId) void client.getReplay(replayId).then((job) => { replay.value = job }).catch(() => localStorage.removeItem('nemwatch-replay-id'))
    socket.start()
  })
  onBeforeUnmount(() => socket.stop())
  return { regions, latest, latestByRegion, history, alerts, selectedRegion, loading, historyLoading, error, announcement, connectionState, replay, replayError, refresh, loadHistory, acknowledgeAlert, startReplay, cancelReplay }
}
