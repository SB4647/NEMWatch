import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ReplayControl from '../../src/components/ReplayControl.vue'

describe('ReplayControl', () => {
  it('disables start while a replay is active and exposes cancellation', () => {
    const wrapper = mount(ReplayControl, { props: {
      regions: [{ code: 'QLD1', name: 'Queensland' }], error: null,
      job: { id: 'one', source: 'dispatch_sample.csv', regions: ['QLD1'], speed: 100, status: 'running', total: 10, processed: 4, published: 4, rejected: 0, current_interval: null, started_at: null, completed_at: null, cancel_requested: false, failure_message: null },
    } })
    expect(wrapper.get('button[type="submit"]').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Cancel replay')
    expect(wrapper.text()).toContain('4 / 10 published')
  })
})
