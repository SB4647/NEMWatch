import type { AlertItem, DispatchObservation, ReplayJob } from './types'

export type MarketMessage =
  | { type: 'dispatch_observed'; data: DispatchObservation }
  | { type: 'alert_raised' | 'alert_acknowledged'; data: AlertItem }
  | { type: 'replay_progress'; data: ReplayJob }

export type ConnectionState = 'connecting' | 'connected' | 'disconnected'

export class MarketSocket {
  private socket: WebSocket | null = null
  private stopped = true
  private attempt = 0

  constructor(
    private readonly url: string,
    private readonly onMessage: (message: MarketMessage) => void,
    private readonly onState: (state: ConnectionState) => void,
  ) {}

  start(): void {
    this.stopped = false
    this.connect()
  }

  stop(): void {
    this.stopped = true
    this.socket?.close()
  }

  private connect(): void {
    if (this.stopped) return
    this.onState('connecting')
    this.socket = new WebSocket(this.url)
    this.socket.onopen = () => { this.attempt = 0; this.onState('connected') }
    this.socket.onmessage = (event) => this.onMessage(JSON.parse(String(event.data)) as MarketMessage)
    this.socket.onclose = () => {
      this.onState('disconnected')
      if (!this.stopped) window.setTimeout(() => this.connect(), Math.min(30_000, 500 * 2 ** this.attempt++))
    }
  }
}

export function marketWebSocketUrl(apiBase: string, pageOrigin = window.location.origin): string {
  const base = (apiBase || pageOrigin).replace(/\/$/, '')
  return `${base.replace(/^http/, 'ws')}/ws/market`
}
