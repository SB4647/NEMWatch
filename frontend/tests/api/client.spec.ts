import { describe, expect, it, vi } from 'vitest'

import { NemWatchClient } from '../../src/api/client'

describe('NemWatchClient', () => {
  it('encodes history query values', async () => {
    const fetchFn = vi.fn().mockResolvedValue(new Response(JSON.stringify({ items: [], limit: 5, offset: 0, has_more: false }), { status: 200, headers: { 'Content-Type': 'application/json' } }))
    const client = new NemWatchClient('http://api.test', fetchFn)
    await client.getHistory('QLD1', '2026-01-01T00:00:00+10:00', '2026-01-01T01:00:00+10:00', 5)
    expect(fetchFn.mock.calls[0][0]).toContain('start=2026-01-01T00%3A00%3A00%2B10%3A00')
  })

  it('turns problem details into ApiError', async () => {
    const fetchFn = vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: { code: 'invalid_range', message: 'Bad range' } }), { status: 422, headers: { 'Content-Type': 'application/json' } }))
    const client = new NemWatchClient('http://api.test', fetchFn)
    await expect(client.getHistory('QLD1', 'a', 'b')).rejects.toEqual(
      expect.objectContaining({ code: 'invalid_range', status: 422 }),
    )
  })
})
