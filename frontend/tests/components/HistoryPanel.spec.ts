import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import HistoryPanel from '../../src/components/HistoryPanel.vue'

describe('HistoryPanel', () => {
  it('renders chart values in an equivalent table', () => {
    const item = { region: 'QLD1' as const, interval_datetime: '2026-09-19T00:00:00Z', price: '94.50', demand: '7150.00', generation: '7025.00', interchange: '125.00' }
    const wrapper = mount(HistoryPanel, { props: { regions: [{ code: 'QLD1', name: 'Queensland' }], items: [item], selectedRegion: 'QLD1', loading: false } })
    expect(wrapper.get('svg').attributes('role')).toBe('img')
    expect(wrapper.get('table').text()).toContain('94.50')
    expect(wrapper.get('table').text()).toContain('7150.00')
  })
})
