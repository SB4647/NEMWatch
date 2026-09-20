import { describe, expect, it } from 'vitest'

import { marketWebSocketUrl } from '../../src/api/live'

describe('marketWebSocketUrl', () => {
  it('uses the dashboard origin when no separate API origin is configured', () => {
    expect(marketWebSocketUrl('', 'http://localhost:5173')).toBe(
      'ws://localhost:5173/ws/market',
    )
  })

  it('keeps an explicitly configured API origin', () => {
    expect(marketWebSocketUrl('https://api.example.test', 'http://localhost:5173')).toBe(
      'wss://api.example.test/ws/market',
    )
  })
})
