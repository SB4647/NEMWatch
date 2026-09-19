import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AlertList from '../../src/components/AlertList.vue'

describe('AlertList', () => {
  it('shows a useful empty state', () => {
    expect(mount(AlertList, { props: { alerts: [] } }).text()).toContain('No alerts have been raised.')
  })
})
