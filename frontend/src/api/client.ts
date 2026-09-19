import type { AlertItem, DispatchObservation, Page, ProblemDetail, RegionCode, RegionInfo, ReplayJob } from './types'

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly code: string,
    message: string,
    readonly fields?: Record<string, string>,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

export class NemWatchClient {
  constructor(
    private readonly baseUrl: string,
    private readonly fetchFn: typeof fetch = fetch,
  ) {}

  private async request<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await this.fetchFn(`${this.baseUrl}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
    const body = await response.json()
    if (!response.ok) {
      const problem = (body.detail ?? body) as ProblemDetail
      throw new ApiError(response.status, problem.code ?? 'request_failed', problem.message ?? 'Request failed', problem.fields)
    }
    return body as T
  }

  getRegions(): Promise<RegionInfo[]> {
    return this.request('/api/v1/regions')
  }

  getLatest(regions: RegionCode[] = []): Promise<DispatchObservation[]> {
    const query = new URLSearchParams()
    regions.forEach((region) => query.append('region', region))
    return this.request(`/api/v1/dispatch/latest${query.size ? `?${query}` : ''}`)
  }

  getHistory(region: RegionCode, start: string, end: string, limit = 500): Promise<Page<DispatchObservation>> {
    const query = new URLSearchParams({ region, start, end, limit: String(limit) })
    return this.request(`/api/v1/dispatch/history?${query}`)
  }

  getAlerts(): Promise<Page<AlertItem>> {
    return this.request('/api/v1/alerts?limit=100&offset=0')
  }

  acknowledgeAlert(id: string, note: string): Promise<AlertItem> {
    return this.request(`/api/v1/alerts/${encodeURIComponent(id)}/acknowledge`, {
      method: 'POST', body: JSON.stringify({ note }),
    })
  }

  startReplay(regions: RegionCode[], speed: number): Promise<ReplayJob> {
    return this.request('/api/v1/replays', {
      method: 'POST', body: JSON.stringify({ source: 'dispatch_sample.csv', regions, speed }),
    })
  }

  getReplay(id: string): Promise<ReplayJob> {
    return this.request(`/api/v1/replays/${encodeURIComponent(id)}`)
  }

  cancelReplay(id: string): Promise<ReplayJob> {
    return this.request(`/api/v1/replays/${encodeURIComponent(id)}`, { method: 'DELETE' })
  }
}

export const api = new NemWatchClient(import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000')
