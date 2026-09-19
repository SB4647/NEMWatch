import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import LiveStatus from '../../src/components/LiveStatus.vue'

describe('LiveStatus', () => {
  it('states the connection status in text', () => {
    const wrapper = mount(LiveStatus, { props: { state: 'connected' } })
    expect(wrapper.text()).toContain('Live updates: connected')
    expect(wrapper.attributes('role')).toBe('status')
  })
})
